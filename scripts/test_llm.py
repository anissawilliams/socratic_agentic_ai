from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm import complete, llm_metadata
from app.socratic.prompts import ELENCHUS_PROMPT

print("llm_metadata:", llm_metadata())

response = complete(
    [
        SystemMessage(content=ELENCHUS_PROMPT),
        HumanMessage(content=(
            "I agree that citation count is popular but I don't agree it proves "
            "quality. A paper could be cited many times for the wrong reasons."
        )),
    ],
)

print(response.content)
