import asyncio
from dotenv import load_dotenv

load_dotenv()

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console

model = OpenAIChatCompletionClient(model="gpt-4o-mini")

clarity_agent = AssistantAgent(
    "ClarityAgent",
    model_client=model,
    system_message="""You are an expert editor focused on clarity and simplicity.
            Your job is to eliminate ambiguity, redundancy, and make every sentence crisp and clear.
            Don't worry about persuasion or tone — just make the message easy to read and understand.""",
)

tone_agent = AssistantAgent(
    "ToneAgent",
    model_client=model,
    system_message="""You are a communication coach focused on emotional tone and professionalism.
            Your job is to make the email sound warm, confident, and human — while staying professional
            and appropriate for the audience. Improve the emotional resonance, polish the phrasing,
            and adjust any words that may come off as stiff, cold, or overly casual.""",
)

persuasion_agent = AssistantAgent(
    "PersuasionAgent",
    model_client=model,
    system_message="""You are a persuasion expert trained in marketing, behavioral psychology,
            and copywriting. Your job is to enhance the email's persuasive power: improve call to action, structure arguments, and emphasize benefits. Remove weak or passive language.""",
)

synthesizer_agent = AssistantAgent(
    "SynthesizerAgent",
    model_client=model,
    system_message="""You are an advanced email-writing specialist. Your role is to read all
            prior agent responses and revisions, and then **synthesize the best ideas** into a unified,
            polished draft of the email. Focus on: Integrating clarity, tone, and persuasion improvements;
            Ensuring coherence, fluency, and a natural voice; Creating a version that feels professional,
            effective, and readable.""",
)

critic_agent = AssistantAgent(
    "CriticAgent",
    model_client=model,
    system_message="""You are an email quality evaluator. Your job is to perform a final review
            of the synthesized email and determine if it meets professional standards. Review the email for:
            Clarity and flow, appropriate professional tone, effective call-to-action, and overall coherence.
            Be constructive but decisive. If the email has major flaws (unclear message, unprofessional tone,
            or missing key elements), provide ONE specific improvement suggestion. If the email meets professional standards and communicates effectively, respond with 'The email meets professional standards.' followed by `TERMINATE` on a new line. You should only approve emails that are perfect enough for professional use, dont settle.""",
)

text_termination = TextMentionTermination("TERMINATE")
max_messages_termination = MaxMessageTermination(max_messages=30)

termination_condition = text_termination | max_messages_termination

team = RoundRobinGroupChat(
    participants=[
        clarity_agent,
        tone_agent,
        persuasion_agent,
        synthesizer_agent,
        critic_agent,
    ],
    termination_condition=termination_condition,
)


async def main():
    await Console(
        team.run_stream(
            task="안녕하세요! 배고프니까 점심 사주시고, 제 사업에 투자해주세요. 감사합니다."
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
