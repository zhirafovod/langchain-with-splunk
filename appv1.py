from openai import OpenAI
from flask import Flask, request
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

app = Flask(__name__)
OpenAIInstrumentor().instrument()
client = OpenAI()

@app.route("/askquestion", methods=['POST'])
def ask_question():

    current_span = trace.get_current_span()  # <-- get a reference to the current span

    try:

        data = request.json
        question = data.get('question')

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": question}
            ]
        )

        return completion.choices[0].message.content

    except Exception as ex:
        current_span.set_status(Status(StatusCode.ERROR))
        current_span.record_exception(ex)

