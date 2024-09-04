from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from flask import Flask, request
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

app = Flask(__name__)
LangchainInstrumentor().instrument()
model = ChatOpenAI(model="gpt-3.5-turbo")

@app.route("/askquestion", methods=['POST'])
def ask_question():

    current_span = trace.get_current_span()  # <-- get a reference to the current span

    try:

        data = request.json
        question = data.get('question')

        messages = [
            SystemMessage(content="You are a helpful assistant!"),
            HumanMessage(content=question),
        ]

        return model.invoke(messages).content

    except Exception as ex:
        current_span.set_status(Status(StatusCode.ERROR))
        current_span.record_exception(ex)

