import asyncio
import dotenv

dotenv.load_dotenv()

from agents import Agent, Runner, SQLiteSession, function_tool, trace
from pydantic import BaseModel

session = SQLiteSession("user_111111", "ai-memory.db")


class Answer(BaseModel):
    answer: str
    background_explanation: str


@function_tool
def get_weather():
    return "30"


geaography_agent = Agent(
    name="Geo Expert Agent",
    instructions="You are a expert in geography, you answer questions related to them.",
    handoff_description="Use this to answer geography related questions.",
    tools=[
        get_weather,
    ],
    output_type=Answer,
)
economics_agent = Agent(
    name="Economics Expert Agent",
    instructions="You are a expert in economics, you answer questions related to them.",
    handoff_description="Use this to answer economics questions.",
)

main_agent = Agent(
    name="Main Agent",
    instructions="You are a user facing agent. Transfer to the agent most capable of answering the user's question.",
    handoffs=[
        economics_agent,
        geaography_agent,
    ],
)


async def main():
    with trace("user_111111"):
        result = await Runner.run(
            main_agent,
            "What is the capital of Colombia's northen province.",
            session=session,
        )
        print(result.final_output)
        result = await Runner.run(
            main_agent,
            "What is the capital of Cambodia's northen province.",
            session=session,
        )
        print(result.final_output)
        result = await Runner.run(
            main_agent,
            "What is the capital of Thailand's northen province.",
            session=session,
        )
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
