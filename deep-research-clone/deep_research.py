import asyncio
from dotenv import load_dotenv

load_dotenv()

from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console
from tools import web_search_tool, save_report_to_md

model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
)

research_planner = AssistantAgent(
    "research_planner",
    description="A strategic research coordinator that breaks down complex questions into research subtasks",
    model_client=model_client,
    system_message="""당신은 리서치 기획 전문가입니다. 집중된 리서치 계획을 작성하세요.

각 연구 질문에 대해 다음을 포함한 집중된 리서치 계획을 작성하세요:

1. **핵심 주제**: 조사할 2-3개의 주요 영역
2. **검색 쿼리**: 다음을 다루는 3-5개의 구체적인 검색 쿼리 작성:
   - 최신 개발 및 뉴스
   - 주요 통계 또는 데이터
   - 전문가 분석 또는 연구
   - 미래 전망

계획은 집중적이고 달성 가능하게 유지하세요. 양보다 질을 우선시하세요.

**모든 응답은 반드시 한글로 작성하세요.**""",
)

research_agent = AssistantAgent(
    "research_agent",
    description="A web research specialist that searches and extracts content",
    tools=[web_search_tool],
    model_client=model_client,
    system_message="""당신은 웹 리서치 전문가입니다. 리서치 계획에 따라 집중된 검색을 수행하세요.

리서치 전략:
1. **리서치 계획에서 3-5개 검색 실행**
2. **결과에서 핵심 정보 추출**:
   - 주요 사실 및 통계
   - 최근 개발 동향
   - 전문가 의견
   - 중요한 맥락

3. **품질 중심**:
   - 신뢰할 수 있는 출처 우선
   - 최근 정보 찾기 (2년 이내)
   - 다양한 관점 파악

계획의 검색을 완료한 후 발견한 내용을 요약하세요. 5-10개의 양질의 출처를 수집하는 것이 목표입니다.

**모든 응답은 반드시 한글로 작성하세요.**""",
)

research_analyst = AssistantAgent(
    "research_analyst",
    description="An expert analyst that creates research reports",
    model_client=model_client,
    system_message="""당신은 리서치 분석가입니다. 수집된 리서치를 바탕으로 종합 보고서를 작성하세요.

다음 구조로 리서치 보고서를 작성하세요:

## 요약
- 주요 발견 및 결론
- 핵심 인사이트

## 배경 및 현황
- 현재 환경
- 최근 개발 동향
- 주요 통계 및 데이터

## 분석 및 인사이트
- 주요 트렌드
- 다양한 관점
- 전문가 의견

## 미래 전망
- 신흥 트렌드
- 예측
- 시사점

## 출처
- 사용된 모든 출처 나열

수집된 리서치를 기반으로 명확하고 잘 구조화된 보고서를 작성하세요.
완료 시 "REPORT_COMPLETE"로 끝내세요.

**모든 응답은 반드시 한글로 작성하세요.**""",
)

quality_reviewer = AssistantAgent(
    "quality_reviewer",
    description="A quality assurance specialist that evaluates research completeness and accuracy",
    tools=[save_report_to_md],
    model_client=model_client,
    system_message="""당신은 품질 검토자입니다. 리서치 분석가가 완전한 리서치 보고서를 작성했는지 확인하세요.

확인 사항:
- "REPORT_COMPLETE"로 끝나는 리서치 분석가의 종합 보고서
- 연구 질문이 완전히 답변되었는지
- 출처가 인용되고 신뢰할 수 있는지
- 보고서에 요약, 핵심 정보, 분석, 출처가 포함되어 있는지

"REPORT_COMPLETE"로 끝나는 완전한 리서치 보고서를 확인하면:
1. 먼저 save_report_to_md 도구를 사용하여 보고서를 report.md에 저장
2. 그런 다음: "리서치가 완료되었습니다. 보고서가 report.md에 저장되었습니다. APPROVED"

리서치 분석가가 아직 완전한 보고서를 작성하지 않았다면, 지금 작성하도록 지시하세요.

**모든 응답은 반드시 한글로 작성하세요.**""",
)

research_enhancer = AssistantAgent(
    "research_enhancer",
    description="A specialist that identifies critical gaps only",
    model_client=model_client,
    system_message="""당신은 리서치 보완 전문가입니다. 오직 중요한 공백만 식별하세요.

리서치를 검토하고 다음과 같은 주요 공백이 있는 경우에만 추가 검색을 제안하세요:
- 최근 개발 동향이 완전히 누락됨 (최근 6개월)
- 통계나 데이터가 전혀 없음
- 특별히 요청된 중요한 관점이 누락됨

리서치가 기본 사항을 합리적으로 잘 다루고 있다면: "리서치가 보고서 작성을 진행하기에 충분합니다."라고 말하세요.

꼭 필요한 경우에만 1-2개의 추가 검색을 제안하세요. 완벽한 커버리지보다 좋은 보고서 완성을 우선시합니다.

**모든 응답은 반드시 한글로 작성하세요.**""",
)

selector_prompt = """
Choose the best agent for the current task based on the conversation history:

{roles}

Current conversation:
{history}

Available agents:
- research_planner: Plan the research approach (ONLY at the start)
- research_agent: Search for and extract content from web sources (after planning)
- research_enhancer: Identify CRITICAL gaps only (use sparingly)
- research_analyst: Write the final research report
- quality_reviewer: Check if a complete report exists and approve

WORKFLOW:
1. If no planning done yet → select research_planner
2. If planning done but no research → select research_agent
3. After research_agent completes initial searches → select research_enhancer ONCE
4. If enhancer says "sufficient to proceed" → select research_analyst
5. If enhancer suggests critical searches → select research_agent ONCE more then research_analyst
6. If research_analyst said "REPORT_COMPLETE" → select quality_reviewer

IMPORTANT: After research_agent has searched 2 times maximum, proceed to research_analyst regardless.

Pick the agent that should work next based on this workflow."""

text_termination = TextMentionTermination("APPROVED")
max_message_termination = MaxMessageTermination(max_messages=50)
termination_condition = text_termination | max_message_termination

team = SelectorGroupChat(
    participants=[
        research_agent,
        research_analyst,
        research_enhancer,
        research_planner,
        quality_reviewer,
    ],
    selector_prompt=selector_prompt,
    model_client=model_client,
    termination_condition=termination_condition,
)


async def main():
    await Console(
        team.run_stream(task="원자력 에너지의 최신 개발 동향에 대해 조사해주세요"),
    )


if __name__ == "__main__":
    asyncio.run(main())
