import os

import httpx
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI


def load_env():
    load_dotenv(".env")
    load_dotenv("../.env")
    # the shared file calls it OPENAI_APIKEY, the OpenAI client looks for OPENAI_API_KEY
    if "OPENAI_API_KEY" not in os.environ and "OPENAI_APIKEY" in os.environ:
        os.environ["OPENAI_API_KEY"] = os.environ["OPENAI_APIKEY"]


def openai_client():
    load_env()
    # httpx drops an idle connection after 5 seconds, so nearly every cell opened a new
    # one, and opening one here can hang for two minutes. Hold connections for 10 minutes
    # and give up on a stalled connect after 3 seconds instead of waiting out the socket.
    return OpenAI(
        http_client=httpx.Client(
            limits=httpx.Limits(max_keepalive_connections=10, keepalive_expiry=600),
            timeout=httpx.Timeout(60.0, connect=3.0),
        ),
        max_retries=5,
    )


def get_driver():
    load_env()
    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        # the vector search procedure reports as deprecated on 2026.07.1 and its
        # replacement does not parse yet, so the warning would print on every call
        notifications_disabled_classifications=["DEPRECATION"],
    )
