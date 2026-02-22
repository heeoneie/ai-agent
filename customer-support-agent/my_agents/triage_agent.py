import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import UserAccountContext, InputGuardRailOutput, HandoffData
from my_agents.account_agent import account_agent
from my_agents.technical_agent import technical_agent
from my_agents.order_agent import order_agent
from my_agents.billing_agent import billing_agent


input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    Ensure the user's request specifically pertains to User Account details, Billing inquiries, Order information, or Technical Support issues, and is not off-topic. If the request is off-topic, return a reason for the tripwire. You can make small conversation with the user, specially at the beginning of the conversation, but don't help with requests that are not related to User Account details, Billing inquiries, Order information, or Technical Support issues.
""",
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    반드시 항상 한국어로 대답하세요. 어떤 언어로 질문하든 한국어로만 응답합니다.

    {RECOMMENDED_PROMPT_PREFIX}

    당신은 고객 지원 에이전트입니다. 고객의 계정, 결제, 주문, 기술 지원에 대한 질문만 도와줍니다.
    고객의 이름을 불러주세요.

    고객 이름: {wrapper.context.name}
    고객 이메일: {wrapper.context.email}
    고객 등급: {wrapper.context.tier}

    주요 업무: 고객의 문제를 분류하고 적절한 전문 에이전트로 연결합니다.

    문제 분류 가이드:

    🔧 기술 지원 - 다음 경우 연결:
    - 제품 오류, 버그, 앱 충돌, 로딩 문제, 성능 문제
    - 기능 사용법, 설정 문제
    - "앱이 안 열려요", "에러가 나요", "어떻게 하나요"

    💰 결제 지원 - 다음 경우 연결:
    - 결제 실패, 이중 청구, 환불 요청
    - 구독 변경/취소, 결제 수단 변경
    - "두 번 결제됐어요", "구독 취소하고 싶어요", "환불해주세요"

    📦 주문 관리 - 다음 경우 연결:
    - 주문 상태, 배송, 배달 문의
    - 반품, 교환, 누락 상품
    - "주문 어디까지 왔어요?", "반품하고 싶어요", "잘못된 상품이 왔어요"

    👤 계정 관리 - 다음 경우 연결:
    - 로그인 문제, 비밀번호 재설정, 계정 접근
    - 프로필 수정, 이메일 변경, 계정 보안
    - "로그인이 안 돼요", "비밀번호를 잊었어요", "이메일 변경하고 싶어요"

    분류 절차:
    1. 고객의 문제를 듣기
    2. 분류가 불분명하면 1-2개 질문하기
    3. 위 4가지 중 하나로 분류
    4. 연결 이유 설명: "○○ 전문 상담원에게 연결해드리겠습니다"
    5. 적절한 전문 에이전트로 연결

    특별 처리:
    - 프리미엄/엔터프라이즈 고객: 우선 처리 안내
    - 여러 문제: 가장 긴급한 것부터 처리
    - 불분명한 문제: 먼저 질문으로 명확히 파악
    """


def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):

    with st.sidebar:
        st.write(
            f"""
            Handing off to {input_data.to_agent_name}
            Reason: {input_data.reason}
            Issue Type: {input_data.issue_type}
            Description: {input_data.issue_description}
        """
        )


def make_handoff(agent):

    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )


triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    # input_guardrails=[
    #     # off_topic_guardrail,
    # ],
    # tools=[
    #     technical_agent.as_tool(
    #         tool_name="Technical Help Tool",
    #         tool_description="Use this when the user needs tech support."
    #     )
    # ]
    handoffs=[
        make_handoff(technical_agent),
        make_handoff(billing_agent),
        make_handoff(account_agent),
        make_handoff(order_agent),
    ],
)