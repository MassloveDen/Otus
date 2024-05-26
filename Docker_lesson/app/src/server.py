from flask import Flask


app = Flask(__name__)


@app.route("/health")
def hello():
    return {"status": "OK"}


# run the application
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=8000)
