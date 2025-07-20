from flask import Flask, request, jsonify, Response
import requests
from ingest_students import ingest_students
import psycopg2
import logging

app = Flask(__name__)
ingest_students()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

@app.route('/api/echo', methods=['GET'])
def echo():
    prompt = request.args.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'Missing prompt query parameter'}), 400

    def generate():
        payload = {
            'model': 'deepseek-r1:14b',
            'prompt': prompt,
            'stream': True
        }
        try:
            with requests.post('http://localhost:11434/api/generate', json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        import json
                        try:
                            data = json.loads(line.decode())
                            if 'response' in data:
                                yield data['response']
                        except Exception:
                            continue
        except Exception as e:
            yield f"ERROR: {str(e)}"

    return Response(generate(), content_type='text/plain')

@app.route('/api/hello', methods=['GET'])
def hello():
    name = request.args.get('name', 'World')
    return jsonify({'message': f'Hello, {name}!'})

@app.route('/api/ask', methods=['GET'])
def ask():
    question = request.args.get('question', '')
    if not question:
        return jsonify({'error': 'Missing question query parameter'}), 400

    # Step 1: Get embedding for the question
    payload = {
        'model': 'deepseek-r1:14b',
        'prompt': question
    }
    try:
        emb_resp = requests.post('http://localhost:11434/api/embeddings', json=payload)
        emb_resp.raise_for_status()
        question_emb = emb_resp.json().get('embedding')
        logger.info(f"Embedding returned from LLM for question: {question_emb}")
        if not question_emb:
            return jsonify({'error': 'No embedding returned for question'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Step 2: Query vector DB for top 3 similar students
    try:
        logger.info(f"Query vector DB for top 3 similar students")
        conn = psycopg2.connect(dbname="buddy-chat-db", user="myuser", password="mypassword", host="localhost", port="5432")
        cur = conn.cursor()
        # Convert embedding list to PostgreSQL vector string
        emb_str = '[' + ','.join(str(x) for x in question_emb) + ']'
        cur.execute(f"""
            SELECT name, hobbies, visited_places, interested_food
            FROM student_vectors
            ORDER BY embedding <-> %s::vector
            LIMIT 3
        """, (emb_str,))
        results = cur.fetchall()
        logger.info(f"Fetched top 3 similar students from vector DB {results}")
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Step 3: Build context from results
    logger.info(f"Building context from results")
    context = "\n".join([
        f"Name: {r[0]}, Hobbies: {', '.join(r[1])}, Places: {', '.join(r[2])}, Food: {', '.join(r[3])}" for r in results
    ])
    logger.info(f"Context built: {context}")
    prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    logger.info(f"Prompt built: {prompt}")
    # Step 4: Get answer from LLM
    try:
        gen_payload = {
            'model': 'deepseek-r1:14b',
            'prompt': prompt,
            'stream': False
        }
        gen_resp = requests.post('http://localhost:11434/api/generate', json=gen_payload)
        gen_resp.raise_for_status()
        answer = gen_resp.json().get('response', '')
        logger.info(f"Answer returned from LLM: {answer}")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    response = jsonify({'answer': answer, 'context': context})
    logger.info(f"Response built: {response}")
    return response

if __name__ == '__main__':
    app.run(debug=True)
