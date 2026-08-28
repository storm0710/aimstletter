from __future__ import annotations


REVIEW_DATE = "2026-08-06"


OFFICIAL_SOURCES = {
    "langchain": (
        ("LangChain overview", "https://docs.langchain.com/oss/python/langchain/overview"),
        ("LangChain agents", "https://docs.langchain.com/oss/python/langchain/agents"),
        ("LangChain structured output", "https://docs.langchain.com/oss/python/langchain/structured-output"),
    ),
    "langgraph": (
        ("LangGraph overview", "https://docs.langchain.com/oss/python/langgraph/overview"),
        ("LangGraph Graph API", "https://docs.langchain.com/oss/python/langgraph/graph-api"),
        ("LangGraph persistence", "https://docs.langchain.com/oss/python/langgraph/persistence"),
        ("LangGraph interrupts", "https://docs.langchain.com/oss/python/langgraph/interrupts"),
        ("LangGraph checkpointers", "https://docs.langchain.com/oss/python/langgraph/checkpointers"),
    ),
    "prompt-engineering": (
        ("OpenAI prompt engineering guide", "https://developers.openai.com/api/docs/guides/prompt-engineering"),
        ("OpenAI structured outputs", "https://developers.openai.com/api/docs/guides/structured-outputs"),
        ("OpenAI GPT-4.1 prompting guide", "https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide"),
    ),
    "context-engineering": (
        ("Anthropic context engineering for agents", "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents"),
        ("LangChain middleware", "https://docs.langchain.com/oss/python/langchain/middleware/built-in"),
        ("LangChain MCP resources", "https://docs.langchain.com/oss/python/langchain/mcp"),
    ),
    "harness-engineering": (
        ("OpenAI Agents SDK guide", "https://developers.openai.com/api/docs/guides/agents"),
        ("OpenAI Agents SDK Python docs", "https://openai.github.io/openai-agents-python/"),
        ("OpenAI Agents SDK guardrails", "https://openai.github.io/openai-agents-python/guardrails/"),
        ("OpenAI Agents SDK tracing", "https://github.com/openai/openai-agents-python/blob/main/docs/tracing.md"),
        ("Codex sandboxing", "https://learn.chatgpt.com/docs/sandboxing"),
        ("Codex approvals and security", "https://learn.chatgpt.com/docs/agent-approvals-security"),
        ("OpenAI skills", "https://developers.openai.com/api/docs/guides/tools-skills"),
    ),
    "loop-engineering": (
        ("OpenAI Agents SDK guide", "https://developers.openai.com/api/docs/guides/agents"),
        ("LangGraph overview", "https://docs.langchain.com/oss/python/langgraph/overview"),
        ("LangGraph thinking guide", "https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph"),
        ("OpenAI prompt engineering guide", "https://developers.openai.com/api/docs/guides/prompt-engineering"),
    ),
    "graph-engineering": (
        ("Neo4j graph database concepts", "https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/"),
        ("Neo4j graph data modeling", "https://neo4j.com/docs/getting-started/data-modeling/"),
        ("W3C PROV overview", "https://www.w3.org/TR/prov-overview/"),
        ("W3C PROV data model", "https://www.w3.org/TR/prov-dm/"),
        ("Mermaid flowchart syntax", "https://mermaid.ai/open-source/syntax/flowchart.html"),
    ),
}



CONFUSION_ROWS = (
    (
        "프롬프트와 컨텍스트",
        "모델에게 어떤 행동을 요구할지 정의",
        "모델이 판단할 때 어떤 정보를 볼지 정의",
        "좋은 프롬프트도 잘못된 컨텍스트를 받으면 틀릴 수 있고, 좋은 컨텍스트도 지시가 모호하면 일관된 결과를 만들기 어렵습니다.",
    ),
    (
        "LangChain과 LangGraph",
        "구성요소 조합과 외부 통합",
        "상태 기반 실행, 분기, 중단과 재개",
        "LangChain은 앱 구성요소를 연결하고, LangGraph는 긴 작업의 상태와 실행 흐름을 제어합니다.",
    ),
    (
        "LangGraph와 그래프 엔지니어링",
        "AI 워크플로 실행 프레임워크",
        "관계 및 의존성 모델링 방법론",
        "LangGraph는 실행 그래프이고, 그래프 엔지니어링은 시스템·데이터·권한 관계를 설계하는 더 넓은 방법입니다.",
    ),
    (
        "하네스와 루프",
        "실행 환경, 도구, 권한과 안전장치",
        "반복 행동, 평가, 전략 변경과 종료 결정",
        "하네스가 루프를 감싸고 제한하며, 루프는 하네스가 제공하는 환경 안에서 실행됩니다.",
    ),
    (
        "컨텍스트와 하네스",
        "모델이 볼 수 있는 정보",
        "에이전트가 사용할 수 있는 실행 환경과 권한",
        "컨텍스트는 판단 재료이고, 하네스는 실제 행동의 경계입니다.",
    ),
    (
        "그래프와 에이전트 엔지니어링",
        "관계와 의존성을 모델링",
        "도구 실행, 평가, 관측, 보안을 운영",
        "그래프는 구조를 이해하는 방법이고, 에이전트 엔지니어링은 그 구조 안에서 AI를 안전하게 운영하는 전체 활동입니다.",
    ),
)


HARNESS_LOOP_ROWS = (
    ("검증", "검증 도구와 통과 규칙을 제공하고 강제", "검증 결과를 보고 다음 행동을 결정"),
    ("비용", "최대 비용과 호출 횟수를 강제로 제한", "남은 비용을 고려해 계속할지 종료할지 판단"),
    ("재시도", "상태 저장과 안전한 재실행 환경을 제공", "언제 무엇을 바꿔 재시도할지 결정"),
    ("로그", "입력, 도구 호출, 결과를 기록", "이전 실행 기록을 다음 판단에 활용"),
    ("사람 승인", "승인 없이 위험한 실행을 차단", "어느 시점에 승인을 요청할지 결정"),
)


KNOWLEDGE_PAGES = {
    "langchain": {
        "difficulty": "초급~중급",
        "audience": "백엔드 · AI 엔지니어 · 기획자",
        "reading_time": "11분",
        "maturity": "실무 활용 가능",
        "updated_at": REVIEW_DATE,
        "volatile": "API와 패키지 구성은 빠르게 바뀔 수 있음",
        "related": ("prompt-engineering", "context-engineering", "langgraph", "harness-engineering"),
        "keywords": ("Model", "Prompt Template", "Retriever", "Tool", "Structured Output"),
        "definition": "모델, 프롬프트, 검색기, 도구, 출력 처리를 하나의 AI 애플리케이션으로 연결하는 컴포넌트 프레임워크입니다.",
        "problem": (
            ("기존 방식", "모델 SDK 호출, 프롬프트 문자열, 검색 API, JSON 파싱, 업무 도구 호출을 각각 직접 붙입니다."),
            ("발생하는 문제", "연결 코드는 빠르게 늘고, 출력 검증과 도구 호출 실패 처리가 여러 파일에 흩어집니다."),
            ("해결 방식", "Prompt Template, Model, Tool, Structured Output 같은 구성요소를 표준 인터페이스로 조합합니다."),
            ("해결하지 못하는 부분", "업무 정책, 데이터 권한, 복잡한 상태 전이는 별도로 설계해야 합니다. 모든 AI 앱에 반드시 필요한 것은 아닙니다."),
        ),
        "components": (
            "Prompt Template이 회의록과 출력 조건을 모델 입력으로 만들고, Model이 초안을 생성합니다. Structured Output은 결정 사항, 담당자, 마감일을 타입이 있는 객체로 받게 하며, Output Validation은 날짜 누락이나 담당자 없는 작업을 막습니다. 마지막으로 Tool 연결이 업무 관리 도구 등록 초안을 만듭니다.",
            ("회의록 입력", "Prompt Template", "Model", "Structured Output", "Validation", "업무 도구 초안"),
        ),
        "use_table": (
            ("모델, 검색기, 도구, 출력 검증을 함께 조합해야 함", "단일 모델 호출로 끝나는 문장 변환", "컴포넌트별 책임과 실패 처리를 나눌 수 있는가", "모델 SDK 직접 호출"),
            ("여러 LLM 제공자나 검색 도구를 바꿔 끼울 가능성이 있음", "프레임워크 종속성을 피해야 하는 핵심 저수준 경로", "팀이 LangChain 추상화를 이해하고 운영할 수 있는가", "작은 서비스 함수와 명시적 어댑터"),
            ("프로토타입을 빠르게 만들고 운영 코드로 다듬어야 함", "성능 병목이 매우 민감한 초고빈도 요청", "추적, 평가, 출력 검증 기준이 있는가", "간단한 파이프라인 스크립트"),
        ),
        "case": {
            "title": "회의록을 업무 등록 초안으로 바꾸기",
            "goal": "회의록에서 요약, 결정 사항, 담당자, 마감일을 구조화하고 업무 관리 도구 등록 초안을 만듭니다.",
            "old_problem": "담당자가 회의록을 읽고 액션 아이템을 수동으로 복사하며, 마감일 표현과 담당자 표기가 매번 달라집니다.",
            "input": "회의 transcript, 참석자 목록, 프로젝트명, 업무 도구의 필드 스키마",
            "steps": ("회의록 정리", "Prompt Template에 회의 정보 삽입", "Model 호출", "Structured Output으로 액션 아이템 수신", "누락 필드 검증", "업무 관리 도구 등록 초안 생성"),
            "tools": "LangChain Prompt Template, Chat Model, Pydantic 구조화 출력, Validation 함수, 업무 도구 API 어댑터",
            "human": "담당자와 마감일이 불확실한 항목은 사람이 확인한 뒤 등록합니다.",
            "failure": "마감일이 '다음 주'처럼 상대 표현이면 기준 날짜 없이 등록하지 않습니다.",
            "output": "요약 5줄, 결정 사항 목록, 담당자·마감일·우선순위가 있는 등록 초안",
            "why": "컴포넌트를 직접 연결할 때보다 입력 템플릿, 모델, 출력 검증, 도구 연결 책임이 분리됩니다.",
            "without": "단순 스크립트는 빠르지만 출력 형식 변경, 도구 교체, 검증 추가 때 코드가 쉽게 얽힙니다.",
        },
        "code_label": "개념 설명용 Python 의사 코드",
        "code": """class ActionItem:
    task: str
    owner: str
    due_date: str | None
    confidence: float

prompt = PromptTemplate(
    template=\"회의록에서 결정 사항과 실행 항목을 추출하라: {transcript}\"
)
model = ChatModel(name=\"검증된 사내 표준 모델\")
parser = StructuredOutput(schema=list[ActionItem])

draft = parser.parse(model.invoke(prompt.format(transcript=minutes)))
valid_items = validate_required_fields(draft, required=(\"task\", \"owner\"))
tool_payload = make_task_tool_payload(valid_items)
preview = task_tool.preview_create(tool_payload)""",
        "code_notes": ("Prompt Template은 입력 변수를 명시해 프롬프트 문자열 조립 오류를 줄입니다.", "Structured Output은 자연어 파싱 대신 타입이 있는 결과를 받기 위한 설계입니다.", "외부 도구는 바로 실행하지 않고 preview 단계에서 사람이 확인할 수 있게 둡니다."),
        "compare": (
            ("모델 SDK 직접 호출", "어떻게 호출할 것인가", "요청·응답 JSON", "간단한 호출 함수", "초소형 기능", "파싱과 검증이 흩어짐", "연결 요소가 적으면 직접 호출이 낫습니다."),
            ("LangGraph", "상태와 분기를 어떻게 실행할 것인가", "State, Node, Edge", "재개 가능한 워크플로", "승인·재시도가 많은 장기 작업", "상태 설계 복잡성", "흐름 제어가 핵심이면 LangGraph를 봅니다."),
            ("단순 스크립트", "정해진 순서를 어떻게 자동화할 것인가", "함수와 순차 로직", "작업 스크립트", "도구 1~2개 연결", "확장 시 조건문 폭증", "프로토타입이면 충분할 수 있습니다."),
        ),
        "failures": (
            ("프레임워크가 문제를 모두 해결한다고 믿음", "업무 정책과 권한 설계가 빠짐", "도구 실행 로그와 오류 유형을 보면 예외가 반복됨", "LangChain은 연결 계층으로 두고 권한·검증은 별도 설계"),
            ("출력 스키마가 자주 깨짐", "모델 지시와 파서 스키마가 어긋남", "파싱 실패율과 재시도율 증가", "스키마를 작게 나누고 예시와 검증 메시지 추가"),
            ("컴포넌트 추상화가 과함", "단순 호출에도 체인과 에이전트를 도입", "디버깅 시 호출 경로가 불명확", "단순 경로는 SDK 직접 호출로 유지"),
        ),
        "checklist": ("모델·프롬프트·도구 책임이 분리되어 있는가", "구조화 출력 실패 시 재시도 또는 사람 검토가 있는가", "외부 도구 실행 전 preview 또는 validation이 있는가", "LangChain 버전과 주요 API 변경 가능성을 기록했는가"),
        "roles": (
            ("기획자", "회의록에서 어떤 필드를 업무로 등록할지와 사람이 확인해야 할 항목을 정의합니다."),
            ("디자이너", "추출 결과의 불확실성, 누락 필드, 등록 전 확인 화면을 설계합니다."),
            ("프론트엔드", "회의록 업로드, 추출 결과 수정, 등록 preview UI를 구현합니다."),
            ("백엔드", "업무 도구 API 어댑터, 검증 함수, 실패 재시도 정책을 구현합니다."),
            ("데이터·AI 엔지니어", "추출 품질 평가셋과 스키마별 실패 유형을 관리합니다."),
            ("플랫폼·보안 담당자", "업무 도구 쓰기 권한과 감사 로그 범위를 제한합니다."),
        ),
        "learning": (
            ("읽기 전에", "LLM 호출, JSON 스키마, API 어댑터 개념"),
            ("다음 문서", "LangGraph, 컨텍스트 엔지니어링"),
            ("빠르게 바뀔 수 있는 부분", "LangChain 패키지 구조, create_agent API, 통합 제공자 목록"),
        ),
    },
    "langgraph": {
        "difficulty": "중급",
        "audience": "백엔드 · AI 엔지니어 · 플랫폼 담당자",
        "reading_time": "12분",
        "maturity": "실무 활용 가능",
        "updated_at": REVIEW_DATE,
        "volatile": "체크포인터, interrupt/resume API는 버전 확인 필요",
        "related": ("langchain", "harness-engineering", "loop-engineering", "graph-engineering"),
        "keywords": ("State", "Node", "Edge", "Checkpoint", "Human-in-the-loop"),
        "definition": "상태를 가진 AI 워크플로를 그래프 구조로 실행하고, 분기·재시도·중단·재개를 관리하는 프레임워크입니다.",
        "problem": (
            ("기존 방식", "장애 대응 절차를 긴 체인이나 if 문으로 이어 붙입니다."),
            ("발생하는 문제", "어느 단계에서 실패했는지, 어떤 로그를 이미 조회했는지, 승인 후 어디서 재개할지 추적하기 어렵습니다."),
            ("해결 방식", "State를 중심으로 Node가 일을 하고 Edge가 다음 단계를 정하며, Checkpoint와 Interrupt가 재개 가능한 흐름을 만듭니다."),
            ("해결하지 못하는 부분", "좋은 상태 스키마와 안전한 진단 명령 목록은 사용자가 직접 설계해야 합니다."),
        ),
        "components": (
            "State는 장애 알림, 심각도, 조회한 로그, 원인 후보, 승인 상태를 담습니다. Node는 분류, 로그 조회, 명령 실행처럼 하나의 책임을 맡고, Edge는 심각도나 검증 결과에 따라 다음 노드를 고릅니다. Checkpoint는 중단 지점을 저장하고 Interrupt는 담당자 승인 전에 실행을 멈춥니다.",
            ("Alert", "Classify Node", "Log Node", "Conditional Edge", "Approval Interrupt", "Resume", "Resolve/Escalate"),
        ),
        "use_table": (
            ("중간 승인 후 같은 상태에서 재개해야 함", "실패하면 처음부터 다시 실행해도 되는 짧은 작업", "thread_id와 체크포인터 저장소를 운영할 수 있는가", "일반 함수 체인"),
            ("분기와 재시도가 업무 규칙의 핵심임", "항상 같은 순서로 실행되는 ETL", "State 스키마를 버전 관리할 수 있는가", "상태 머신 라이브러리"),
            ("LLM 판단과 결정적 코드를 섞어야 함", "단순 챗봇 답변", "노드별 테스트와 관측 로그가 있는가", "LangChain agent"),
        ),
        "case": {
            "title": "서비스 장애 대응 에이전트",
            "goal": "장애 알림을 받아 심각도를 분류하고 로그를 조회한 뒤 안전한 진단 명령만 실행해 담당자 승인으로 이어갑니다.",
            "old_problem": "운영자가 알림, 대시보드, 로그, 런북을 오가며 같은 확인 절차를 반복합니다.",
            "input": "장애 알림, 서비스명, 최근 배포 정보, 로그 조회 권한, 런북",
            "steps": ("장애 알림 수신", "심각도 분류", "관련 로그 조회", "원인 후보 생성", "안전한 진단 명령 실행", "결과 평가", "담당자 승인 요청", "해결 또는 에스컬레이션", "중단된 작업 재개"),
            "tools": "StateGraph, Conditional Edge, Checkpoint, interrupt/resume, Human-in-the-loop 승인, 읽기 전용 로그 도구",
            "human": "재시작, 트래픽 차단, 롤백 같은 영향 있는 조치 전 담당자 승인을 요청합니다.",
            "failure": "로그 도구가 실패하면 같은 노드만 재시도하고, 심각도 high이면 즉시 에스컬레이션합니다.",
            "output": "원인 후보, 실행한 진단, 승인 요청 메시지, 재개 가능한 thread id",
            "why": "승인 대기와 장애 재개가 핵심이므로 상태 기반 그래프가 선형 체인보다 적합합니다.",
            "without": "긴 체인은 승인 후 어디서 이어갈지 애플리케이션 코드가 별도로 기억해야 합니다.",
        },
        "code_label": "개념 설명용 LangGraph 스타일 의사 코드",
        "code": """class IncidentState:
    alert: dict
    severity: str
    logs: list[str]
    hypotheses: list[str]
    approval: str | None

graph = StateGraph(IncidentState)
graph.add_node(\"classify\", classify_severity)
graph.add_node(\"read_logs\", fetch_related_logs)
graph.add_node(\"diagnose\", propose_safe_diagnostics)
graph.add_node(\"approval\", ask_human_with_interrupt)
graph.add_conditional_edges(\"classify\", route_by_severity)
graph.add_edge(\"read_logs\", \"diagnose\")
graph.add_edge(\"diagnose\", \"approval\")

app = graph.compile(checkpointer=durable_checkpointer)
app.invoke({\"alert\": alert}, config={\"configurable\": {\"thread_id\": incident_id}})
app.invoke(Command(resume=\"approved\"), config={\"configurable\": {\"thread_id\": incident_id}})""",
        "code_notes": ("State에는 재개에 필요한 최소 정보를 넣습니다.", "Node는 작게 나누어 체크포인트와 테스트 단위를 분명히 합니다.", "Interrupt는 위험한 조치 전 실행을 멈추고, 같은 thread_id로 resume합니다."),
        "compare": (
            ("LangChain 선형 체인", "컴포넌트를 어떤 순서로 연결할 것인가", "입력과 출력", "체인", "고정 순서 처리", "중단 후 재개가 약함", "분기·승인이 적으면 충분합니다."),
            ("일반 상태 머신", "상태 전이를 어떻게 정의할 것인가", "상태와 이벤트", "상태 전이표", "결정적 업무 흐름", "LLM·도구 통합을 직접 구현", "AI 호출이 부가 기능이면 고려합니다."),
            ("그래프 엔지니어링", "관계와 의존성을 어떻게 모델링할 것인가", "업무·데이터·권한 관계", "영향도 그래프", "시스템 분석", "실행 런타임이 아님", "실행보다 관계 분석이 핵심이면 별개로 설계합니다."),
        ),
        "failures": (
            ("State가 너무 큼", "모든 로그와 원문을 상태에 저장", "체크포인트 크기와 재개 시간이 증가", "요약과 참조 ID만 저장"),
            ("노드가 너무 큼", "여러 외부 호출을 한 노드에 몰아넣음", "실패 시 처음부터 재실행", "외부 서비스별 노드로 분리"),
            ("Interrupt 후 재개 실패", "thread_id나 체크포인터 구성이 빠짐", "승인 후 새 실행처럼 시작됨", "체크포인터와 thread_id를 필수 운영값으로 관리"),
        ),
        "checklist": ("State 스키마와 버전 변경 정책이 있는가", "각 Node를 독립 테스트할 수 있는가", "Checkpoint 저장소가 운영 장애에도 안전한가", "Interrupt 승인 메시지와 resume 입력이 기록되는가", "LangGraph와 그래프 엔지니어링의 책임을 문서에서 구분했는가"),
        "roles": (
            ("기획자", "장애 등급, 승인 필요 조치, 에스컬레이션 기준을 정의합니다."),
            ("디자이너", "진행 단계, 승인 대기, 재개 상태를 운영자가 이해할 수 있게 설계합니다."),
            ("프론트엔드", "실행 상태 스트림, 승인 버튼, 재개 결과 표시를 구현합니다."),
            ("백엔드", "StateGraph 노드, 체크포인터, 로그 도구, 에스컬레이션 API를 연결합니다."),
            ("데이터·AI 엔지니어", "원인 후보 생성 품질과 오탐/미탐 평가셋을 만듭니다."),
            ("플랫폼·보안 담당자", "진단 명령 allowlist와 쓰기 조치 승인 정책을 관리합니다."),
        ),
        "learning": (
            ("읽기 전에", "상태 머신, 비동기 작업, 장애 대응 런북"),
            ("다음 문서", "하네스 엔지니어링, 루프 엔지니어링, 그래프 엔지니어링"),
            ("빠르게 바뀔 수 있는 부분", "LangGraph persistence, interrupt/resume, 배포 런타임 API"),
        ),
    },
    "prompt-engineering": {
        "difficulty": "초급",
        "audience": "기획자 · 디자이너 · 개발자 · AI 엔지니어",
        "reading_time": "10분",
        "maturity": "실무 활용 가능",
        "updated_at": REVIEW_DATE,
        "volatile": "모델별 권장 프롬프트 패턴은 변경될 수 있음",
        "related": ("context-engineering", "langchain", "loop-engineering"),
        "keywords": ("Role", "Goal", "Constraint", "Few-shot", "Output Schema"),
        "definition": "모델이 어떤 기준과 형식으로 답해야 하는지 지시문의 품질과 구조를 설계하는 분야입니다.",
        "problem": (
            ("기존 방식", "회의록을 붙여 넣고 '할 일 정리해줘'처럼 막연히 요청합니다."),
            ("발생하는 문제", "담당자 없는 항목, 추측한 마감일, 다른 출력 형식이 반복됩니다."),
            ("해결 방식", "역할, 목표, 제약 조건, 예시, 출력 스키마, 평가 기준을 지시문에 명시합니다."),
            ("해결하지 못하는 부분", "모델이 볼 자료가 부족하거나 악성 입력이 섞인 문제는 컨텍스트와 코드 검증이 필요합니다."),
        ),
        "components": (
            "역할은 모델의 관점을 제한하고, 목표는 완료 기준을 정합니다. 제약 조건은 추측 금지와 예외 처리를 만들고, Few-shot 예시는 원하는 판단 방식을 보여줍니다. 출력 스키마는 애플리케이션 코드가 결과를 검증할 수 있게 합니다.",
            ("Role", "Goal", "Constraints", "Examples", "Schema", "Eval Cases"),
        ),
        "use_table": (
            ("답변 형식과 판단 기준이 흔들림", "모델이 모르는 내부 정보가 필요한 질문", "좋은/나쁜 예시와 평가 기준이 있는가", "UI 폼 검증 또는 코드 후처리"),
            ("같은 업무를 여러 사람이 반복 요청함", "정확한 최신 문서 검색이 핵심인 업무", "프롬프트 버전을 저장할 위치가 있는가", "컨텍스트 엔지니어링"),
            ("모델 출력이 후속 시스템 입력으로 쓰임", "정답이 규칙 엔진으로 충분히 결정됨", "스키마 검증 실패를 처리할 수 있는가", "규칙 기반 파서"),
        ),
        "case": {
            "title": "회의록에서 실행 항목 추출 프롬프트 개선",
            "goal": "회의록에서 실행 항목, 담당자, 마감일, 의존성을 안정적으로 뽑습니다.",
            "old_problem": "모호한 프롬프트는 논의 주제와 실제 할 일을 섞고, 없는 담당자를 추측합니다.",
            "input": "회의록 원문, 참석자 목록, 오늘 날짜, 출력 JSON 스키마",
            "steps": ("모호한 프롬프트로 기준선 생성", "역할·제약·출력 형식 추가", "Few-shot 예시 추가", "나쁜 결과 예시로 평가", "버전 저장"),
            "tools": "프롬프트 템플릿, 구조화 출력 스키마, 프롬프트 테스트 fixture, 버전 로그",
            "human": "불확실한 담당자와 상대 날짜는 회의 주관자가 확인합니다.",
            "failure": "프롬프트 인젝션 문구가 회의록 안에 있어도 시스템 지시를 덮어쓰지 않아야 합니다.",
            "output": "action_items JSON, confidence, needs_review 플래그, 누락 이유",
            "why": "문제는 도구 연결보다 지시 품질과 출력 기준의 불안정성이므로 프롬프트 개선이 먼저입니다.",
            "without": "컨텍스트를 많이 넣어도 지시가 모호하면 결과 형식은 계속 흔들립니다.",
        },
        "code_label": "프롬프트 버전 비교 예시",
        "code": """# v1: 모호함
\"이 회의록에서 할 일을 정리해줘.\"

# v2: 역할, 기준, 출력 형식
\"\"\"당신은 PMO 보조자입니다.
회의록에서 실제 실행 항목만 추출하세요.
담당자나 마감일이 없으면 추측하지 말고 null로 두세요.
출력은 action_items JSON 배열만 반환하세요.\"\"\"

# v3: 예시와 평가 기준 추가
\"\"\"좋은 예:
입력: '민수님이 금요일까지 배포 체크리스트 작성'
출력: {\"task\":\"배포 체크리스트 작성\",\"owner\":\"민수\",\"due_date\":\"이번 주 금요일\"}

나쁜 예: 논의 주제를 실행 항목으로 만들기
평가 기준: 추측 금지, JSON 유효성, 담당자 누락 표시\"\"\"""",
        "code_notes": ("v1은 목표와 형식이 없어 결과가 흔들립니다.", "v2는 역할과 제약 조건으로 추측을 줄입니다.", "v3는 예시와 평가 기준으로 반복 테스트가 가능해집니다."),
        "compare": (
            ("컨텍스트 엔지니어링", "어떤 정보를 볼 것인가", "문서·메모리·권한", "컨텍스트 구성", "내부 자료 기반 답변", "정보 과다/오래됨", "자료 품질 문제가 크면 컨텍스트가 우선입니다."),
            ("파인튜닝", "모델 행동을 학습으로 바꿀 것인가", "학습 데이터", "새 모델 또는 어댑터", "대량 반복 패턴", "비용과 갱신 부담", "프롬프트로 한계가 명확할 때 고려합니다."),
            ("애플리케이션 코드 검증", "출력을 어떻게 강제할 것인가", "스키마와 validator", "검증 로직", "시스템 입력 보호", "사용자 경험 저하", "실패를 허용할 수 없으면 코드 검증이 필수입니다."),
        ),
        "failures": (
            ("출력 형식이 매번 달라짐", "스키마와 예시가 없음", "JSON 파싱 실패율 증가", "구조화 출력과 fixture 테스트 추가"),
            ("모델이 없는 정보를 추측", "추측 금지와 불확실성 처리 규칙이 없음", "원문에 없는 담당자·날짜 생성", "null과 needs_review 규칙 명시"),
            ("프롬프트 인젝션에 흔들림", "입력 문서 안의 지시를 구분하지 않음", "회의록 문구가 시스템 규칙을 바꿈", "데이터와 지시를 구분하고 코드 검증 적용"),
        ),
        "checklist": ("역할과 목표가 첫 문단에 명확한가", "추측 금지와 예외 처리 규칙이 있는가", "출력 스키마와 좋은/나쁜 예시가 있는가", "프롬프트 버전과 평가 결과를 기록하는가", "인젝션성 입력을 테스트했는가"),
        "roles": (
            ("기획자", "추출해야 할 업무 기준과 예외 처리 정책을 정의합니다."),
            ("디자이너", "불확실한 항목을 사용자가 수정하는 흐름을 설계합니다."),
            ("프론트엔드", "스키마 오류와 검토 필요 상태를 UI에 표시합니다."),
            ("백엔드", "프롬프트 버전, structured output, validator를 연결합니다."),
            ("데이터·AI 엔지니어", "평가 fixture와 회귀 테스트를 운영합니다."),
            ("플랫폼·보안 담당자", "프롬프트 인젝션 테스트와 민감정보 마스킹 정책을 점검합니다."),
        ),
        "learning": (
            ("읽기 전에", "LLM 기본 동작, JSON, 테스트 fixture"),
            ("다음 문서", "컨텍스트 엔지니어링, LangChain"),
            ("빠르게 바뀔 수 있는 부분", "모델별 권장 지시 형식, structured output 지원 방식"),
        ),
    },
    "context-engineering": {
        "difficulty": "중급",
        "audience": "데이터 · AI 엔지니어 · 백엔드 · 보안 담당자",
        "reading_time": "12분",
        "maturity": "실무 활용 가능",
        "updated_at": REVIEW_DATE,
        "volatile": "모델 컨텍스트 한도, 검색·재정렬 모델, 권한 정책은 자주 바뀜",
        "related": ("prompt-engineering", "langchain", "graph-engineering"),
        "keywords": ("Retriever", "Metadata", "Rerank", "Token Budget", "Permission Filter"),
        "definition": "모델이 답변을 만들 때 필요한 정보와 상태를 어떤 순서와 범위로 제공할지 설계하는 분야입니다.",
        "problem": (
            ("기존 방식", "사용자 질문과 검색 결과 몇 개를 그대로 프롬프트에 붙입니다."),
            ("발생하는 문제", "권한 없는 문서, 오래된 정책, 관련 없는 긴 문서가 답변을 오염시킵니다."),
            ("해결 방식", "질문 분석, 권한 필터, 메타데이터 검색, 최신성 우선, 재정렬, 요약, 토큰 예산 관리를 적용합니다."),
            ("해결하지 못하는 부분", "잘못 작성된 원문 문서나 없는 정책은 컨텍스트 설계만으로 해결되지 않습니다."),
        ),
        "components": (
            "질문 분석은 필요한 정책 범주를 찾고, 권한 필터는 볼 수 없는 문서를 제거합니다. 검색과 재정렬은 관련 문서를 좁히고, 대화 요약은 현재 의도만 남깁니다. 토큰 예산은 최신·권한·근거 문서가 먼저 들어가도록 우선순위를 정합니다.",
            ("질문 분석", "권한 확인", "문서 검색", "메타데이터 필터", "재정렬", "토큰 예산", "근거 답변"),
        ),
        "use_table": (
            ("사내 정책, 매뉴얼, 고객 이력 등 근거가 필요함", "상식적 답변이나 간단한 문장 변환", "문서 메타데이터와 권한 체계가 있는가", "프롬프트만 개선"),
            ("사용자별로 볼 수 있는 자료가 다름", "모든 사용자가 같은 공개 문서를 봄", "권한 필터를 검색 전에 적용할 수 있는가", "정적 FAQ"),
            ("최신 문서와 오래된 문서가 섞임", "정책 변경이 거의 없음", "최종 수정일과 버전이 관리되는가", "고정 문서 링크 제공"),
        ),
        "case": {
            "title": "사내 정책·매뉴얼 업무 지원 챗봇",
            "goal": "직원이 휴가, 구매, 보안 정책을 질문하면 권한에 맞는 최신 문서 근거로 답합니다.",
            "old_problem": "키워드 검색은 오래된 매뉴얼을 먼저 보여주고, 사용자는 자신에게 적용되는 정책인지 판단하기 어렵습니다.",
            "input": "사용자 질문, 부서·직급·지역 권한, 문서 메타데이터, 대화 요약",
            "steps": ("질문 의도 분석", "사용자 권한 확인", "문서 검색", "메타데이터 필터", "최신 문서 우선 재정렬", "대화 내용 요약", "토큰 예산 배분", "근거 부족 시 답변 제한"),
            "tools": "검색 인덱스, 권한 서비스, reranker, 대화 요약기, 출처 표시 컴포넌트",
            "human": "근거가 부족하거나 정책 충돌이 있으면 담당 부서 문의로 전환합니다.",
            "failure": "오래된 정책이 높은 점수를 받거나 권한 없는 문서가 컨텍스트에 들어가는 상황입니다.",
            "output": "짧은 답변, 적용 조건, 출처 문서, 문서 날짜, 추가 확인 필요 여부",
            "why": "문제는 지시문보다 모델이 볼 자료의 품질과 순서입니다.",
            "without": "프롬프트가 좋아도 오래된 문서를 넣으면 답변은 오래된 정책을 따릅니다.",
        },
        "code_label": "컨텍스트 구성 의사 코드",
        "code": """intent = classify_question(user_question)
allowed_scopes = permission_service.scopes(user_id)

docs = search_index.query(
    query=intent.search_query,
    filters={\"scope\": allowed_scopes, \"status\": \"active\"}
)
fresh_docs = prefer_latest(docs, field=\"updated_at\")
ranked = rerank(user_question, fresh_docs)
conversation_note = summarize_recent_turns(history, max_tokens=500)
context = pack_context(
    ranked[:5],
    conversation_note,
    token_budget=6000,
    require_citations=True,
)

if context.has_weak_evidence:
    return limited_answer_with_escalation(context.gaps)""",
        "code_notes": ("권한 필터는 검색 전 또는 검색 중에 적용해야 합니다.", "많이 넣는 것보다 최신성, 관련성, 권한, 근거성을 기준으로 줄이는 것이 중요합니다.", "근거 부족은 답변 제한 조건으로 다룹니다."),
        "compare": (
            ("프롬프트 엔지니어링", "어떻게 지시할 것인가", "역할·형식·예시", "프롬프트 템플릿", "형식 안정화", "자료 부족", "정보가 충분하면 프롬프트부터 봅니다."),
            ("RAG", "검색 자료를 어떻게 붙일 것인가", "검색 인덱스와 문서 조각", "검색 증강 답변", "문서 기반 QA", "검색 품질 의존", "컨텍스트 엔지니어링의 한 구성요소로 봅니다."),
            ("메모리/파인튜닝", "무엇을 저장하거나 학습할 것인가", "사용자 선호·학습 데이터", "장기 기억 또는 모델 변경", "반복 패턴", "오래된 기억과 갱신 비용", "자주 바뀌는 정책은 검색 컨텍스트가 낫습니다."),
        ),
        "failures": (
            ("컨텍스트가 길수록 좋아진다고 믿음", "관련 없는 문서까지 모두 주입", "답변이 장황하고 근거가 흐려짐", "재정렬과 토큰 예산으로 줄임"),
            ("권한 없는 문서 노출", "검색 후 필터링 또는 필터 누락", "출처에 접근 불가 문서가 표시됨", "검색 단계에서 권한 필터 강제"),
            ("오래된 정책 답변", "최신성 메타데이터가 없음", "폐기 문서를 출처로 인용", "문서 상태와 updated_at 필드 필수화"),
        ),
        "checklist": ("문서별 소유자, 상태, 최종 수정일이 있는가", "검색 전에 권한 필터가 적용되는가", "오래된 정보 제거 정책이 있는가", "출처와 문서 날짜를 답변에 표시하는가", "근거 부족 시 답변 제한이 있는가", "토큰 예산 초과 시 우선순위가 정의되어 있는가"),
        "roles": (
            ("기획자", "정책 답변에서 반드시 보여야 할 적용 조건과 출처 표시 기준을 정합니다."),
            ("디자이너", "출처, 최신성, 근거 부족, 담당 부서 문의 UI를 설계합니다."),
            ("프론트엔드", "출처 펼침, 문서 권한 오류, 대화 요약 표시를 구현합니다."),
            ("백엔드", "검색 API, 권한 필터, 캐시, 문서 버전 관리를 연결합니다."),
            ("데이터·AI 엔지니어", "검색 평가셋, reranker 품질, hallucination 사례를 관리합니다."),
            ("플랫폼·보안 담당자", "문서 접근권한과 로그의 민감정보 저장 여부를 점검합니다."),
        ),
        "learning": (
            ("읽기 전에", "검색 인덱스, 임베딩, 토큰, 권한 모델"),
            ("다음 문서", "LangChain, 그래프 엔지니어링, 하네스 엔지니어링"),
            ("빠르게 바뀔 수 있는 부분", "컨텍스트 윈도 크기, reranker 모델, 문서 권한 시스템"),
        ),
    },
    "harness-engineering": {
        "difficulty": "중급~고급",
        "audience": "플랫폼 · 보안 · 백엔드 · AI 엔지니어",
        "reading_time": "13분",
        "maturity": "이 사이트의 실무적 분류. 표준 학술 분류처럼 단정하지 않음",
        "updated_at": REVIEW_DATE,
        "volatile": "Codex, Agents SDK, Claude Code, gstack 기능은 현재 문서 확인 필요",
        "related": ("loop-engineering", "langgraph", "prompt-engineering"),
        "keywords": ("Tool Registry", "Sandbox", "Validation", "Approval", "Audit Log"),
        "definition": "에이전트를 둘러싼 실행 환경, 도구, 권한, 샌드박스, 검증, 승인, 로그를 설계하는 분야입니다.",
        "problem": (
            ("기존 방식", "AI에게 코드 수정과 테스트 실행을 허용하지만, 어떤 파일과 명령을 허용할지 명확히 제한하지 않습니다."),
            ("발생하는 문제", "비밀 정보 노출, 광범위한 파일 수정, 위험한 명령 실행, 감사 불가, 비용 폭증이 생길 수 있습니다."),
            ("해결 방식", "도구 목록, Tool Schema, 읽기·쓰기 권한, sandbox, validators, approval, audit log, limits를 실행 전후로 강제합니다."),
            ("해결하지 못하는 부분", "에이전트가 어떤 전략으로 문제를 풀지는 루프 설계가 담당합니다. 하네스는 환경과 경계입니다."),
        ),
        "components": (
            "Tool Registry는 사용할 도구를 등록하고, Tool Schema는 입력 형식을 제한합니다. Permissions와 Sandbox는 읽기·쓰기 범위를 줄이고, Validators는 테스트와 정책 통과를 강제합니다. Approval은 위험한 변경을 멈추며, Audit Log와 Limits는 사후 추적과 비용 통제를 담당합니다.",
            ("요청", "Tool Registry", "Permissions", "Sandbox", "Validators", "Approval", "Audit Log"),
        ),
        "use_table": (
            ("에이전트가 파일, 저장소, 테스트, 외부 API를 실행함", "읽기 전용 설명이나 초안 생성", "허용 도구와 금지 도구가 문서화되어 있는가", "단순 API 키 제한"),
            ("코드 변경이 운영 품질에 영향을 줌", "개인 로컬 실험", "테스트와 리뷰 gate가 있는가", "사람이 직접 실행"),
            ("보안·감사·비용 통제가 필요함", "일회성 내부 데모", "로그 보존과 승인 책임자가 있는가", "수동 체크리스트"),
        ),
        "case": {
            "title": "코딩 에이전트를 안전하게 운영하는 개발 하네스",
            "goal": "Codex, Claude Code 같은 코딩 에이전트가 저장소에서 작업할 때 허용 도구, 권한, 검증, 승인, 로그를 통제합니다.",
            "old_problem": "에이전트가 편리한 명령을 임의로 실행하거나 넓은 파일 범위를 수정해도 나중에 이유를 추적하기 어렵습니다.",
            "input": "작업 요청, 저장소 경로, 허용 파일 범위, 테스트 명령, 비밀 정보 정책, 승인자",
            "steps": ("도구 등록", "읽기·쓰기 권한 분리", "sandbox 설정", "수정 가능 파일 범위 제한", "테스트 validator 실행", "독립 리뷰", "사람 승인", "감사 로그 저장", "실패 시 복구"),
            "tools": "Codex sandbox/approval 문서, OpenAI Agents SDK guardrails/tracing 문서, Codex Skills 문서. gstack은 로컬 도구로만 확인했으며 공식 공개 출처는 추가 검증 필요.",
            "human": "쓰기, 삭제, 배포, 권한 변경, 비용 큰 명령은 승인 후 실행합니다.",
            "failure": "테스트 실패, 금지 경로 수정, 비밀값 출력, 시간·비용 초과, 리뷰 실패입니다.",
            "output": "허용된 변경 diff, 테스트 결과, 리뷰 결과, 승인 기록, 실행 로그",
            "why": "문제의 중심은 '어떻게 반복할지'가 아니라 '무엇을 허용하고 어떻게 막을지'입니다.",
            "without": "루프가 좋아도 하네스가 없으면 같은 실패를 더 빠르게 반복하거나 위험한 작업을 실행할 수 있습니다.",
        },
        "code_label": "하네스 정책 의사 코드",
        "code": """harness = {
    \"tools\": {
        \"read_file\": {\"mode\": \"read\"},
        \"edit_file\": {\"mode\": \"write\", \"schema\": EditFileSchema},
        \"run_tests\": {\"mode\": \"execute\", \"allow\": [\"pytest\", \"npm test\"]},
    },
    \"permissions\": {
        \"read\": [\"src/**\", \"tests/**\", \"docs/**\"],
        \"write\": [\"src/feature/**\", \"tests/feature/**\"],
        \"deny\": [\".env\", \"secrets/**\", \"infra/prod/**\"],
    },
    \"sandbox\": {\"network\": \"off_by_default\", \"filesystem\": \"project_scoped\"},
    \"validators\": [\"unit_tests_pass\", \"no_secret_output\", \"diff_within_scope\"],
    \"approval\": {\"required_for\": [\"delete\", \"deploy\", \"write_outside_scope\"]},
    \"audit_log\": [\"input\", \"tool_call\", \"diff\", \"test_result\", \"approval\"],
    \"limits\": {\"max_tool_calls\": 40, \"max_minutes\": 20, \"max_cost_usd\": 3.0},
}""",
        "code_notes": ("하네스 코드는 tools, permissions, sandbox, validators, approval, audit log, limits를 중심으로 둡니다.", "구체 명령어는 공식 문서나 저장소에서 확인된 경우만 운영 문서에 넣습니다.", "gstack 연동은 이 환경의 로컬 스킬로 확인했지만 공개 공식 출처는 추가 검증 필요로 표시합니다."),
        "compare": (
            ("루프 엔지니어링", "다음 행동과 종료를 어떻게 결정할 것인가", "상태, 관찰, 평가", "반복 정책", "테스트 실패 수정", "무한 반복", "행동 전략이 문제면 루프입니다."),
            ("LangGraph", "상태 기반 흐름을 어떻게 실행할 것인가", "State, Node, Edge", "워크플로 런타임", "승인·재개", "상태 복잡성", "실행 흐름 자체가 복잡하면 LangGraph입니다."),
            ("보안 정책", "무엇을 금지할 것인가", "규정과 통제", "정책 문서", "조직 리스크 관리", "개발 흐름과 분리", "에이전트 실행에 붙이면 하네스가 됩니다."),
        ),
        "failures": (
            ("허용 도구가 너무 넓음", "Tool Registry 없이 쉘 전체를 허용", "예상 밖 명령과 파일 접근 로그", "도구 allowlist와 schema 적용"),
            ("테스트 없이 변경 승인", "validator가 선택 사항임", "배포 후 회귀 발생", "테스트 통과를 merge gate로 강제"),
            ("감사 로그가 없음", "도구 호출과 승인 기록을 저장하지 않음", "문제 발생 후 원인 추적 불가", "입력, diff, 도구 호출, 결과, 승인 기록 보존"),
        ),
        "checklist": ("도구별 schema와 allowlist가 있는가", "읽기·쓰기·실행 권한이 분리되어 있는가", "sandbox 범위가 프로젝트로 제한되는가", "비밀정보가 프롬프트나 로그에 남지 않는가", "테스트, 리뷰, 승인 gate가 강제되는가", "비용·시간·호출 한도가 있는가", "실패 시 되돌릴 절차가 있는가"),
        "roles": (
            ("기획자", "자동화할 수 있는 작업과 사람이 승인해야 하는 작업을 구분합니다."),
            ("디자이너", "승인 요청, 위험 경고, 테스트 실패 상태를 명확하게 보여줍니다."),
            ("프론트엔드", "diff preview, 승인 버튼, 로그 조회 UI를 구현합니다."),
            ("백엔드", "도구 registry, validator, audit log 저장소를 구현합니다."),
            ("데이터·AI 엔지니어", "에이전트 실패 유형과 validator 효과를 평가합니다."),
            ("플랫폼·보안 담당자", "sandbox, 비밀정보, 네트워크, 권한 정책을 관리합니다."),
        ),
        "learning": (
            ("읽기 전에", "권한 모델, CI 테스트, 코드 리뷰, 샌드박스"),
            ("다음 문서", "루프 엔지니어링, LangGraph"),
            ("추가 검증 필요", "gstack의 공개 공식 저장소와 현재 지원 명령은 이 작업에서 확인하지 못했습니다."),
            ("빠르게 바뀔 수 있는 부분", "Codex sandbox/approval, Agents SDK guardrails/tracing, Skills 사양"),
        ),
    },
    "loop-engineering": {
        "difficulty": "중급",
        "audience": "AI 엔지니어 · 백엔드 · QA · 리더",
        "reading_time": "11분",
        "maturity": "이 사이트의 실무적 분류. 에이전트 제어 패턴으로 설명",
        "updated_at": REVIEW_DATE,
        "volatile": "에이전트 런타임의 loop/approval 처리 방식은 도구별로 바뀔 수 있음",
        "related": ("harness-engineering", "langgraph", "prompt-engineering"),
        "keywords": ("Plan", "Observe", "Evaluate", "Repair", "Stop Condition"),
        "definition": "에이전트가 실행 결과를 관찰하고 수정과 재시도를 반복하는 제어 구조를 설계하는 분야입니다.",
        "problem": (
            ("기존 방식", "AI가 한 번 수정안을 만들고 사람이 테스트 실패를 다시 설명합니다."),
            ("발생하는 문제", "같은 실패를 반복하거나, 언제 멈춰야 할지 몰라 비용과 시간이 늘어납니다."),
            ("해결 방식", "Goal, State, Plan, Act, Observe, Evaluate, Repair, Re-plan, Stop Condition을 명시합니다."),
            ("해결하지 못하는 부분", "허용 도구, 권한, 샌드박스 같은 안전 경계는 하네스가 제공해야 합니다."),
        ),
        "components": (
            "Goal은 성공 기준을 정하고 State는 현재 실패와 시도 이력을 담습니다. Plan은 다음 전략, Act는 실제 수정, Observe는 테스트 결과 수집, Evaluate는 진전 여부 판단입니다. No-progress Detection은 같은 오류 반복을 찾고, Stop Condition은 성공·예산 초과·사람 전달을 결정합니다.",
            ("Goal", "Plan", "Act", "Observe", "Evaluate", "Repair/Re-plan", "Stop/Escalate"),
        ),
        "use_table": (
            ("테스트 결과를 보고 코드를 고쳐야 함", "정답이 한 번에 계산되는 작업", "성공 기준과 관찰 신호가 명확한가", "단일 프롬프트 또는 스크립트"),
            ("실패 원인에 따라 전략을 바꿔야 함", "실패 시 사람이 바로 판단해야 하는 고위험 업무", "최대 반복과 비용 한도가 있는가", "수동 디버깅"),
            ("진전 없는 반복을 감지해야 함", "평가 신호가 없는 창작 업무", "동일 실패 signature를 기록하는가", "사람 검토 중심 흐름"),
        ),
        "case": {
            "title": "테스트에 실패한 코드를 에이전트가 수정하는 반복 과정",
            "goal": "실패한 테스트를 통과시키되, 같은 실패 반복과 비용 초과를 막습니다.",
            "old_problem": "에이전트가 오류 메시지를 보고 계속 비슷한 수정을 하거나, 전체 테스트를 너무 자주 실행합니다.",
            "input": "실패 로그, 변경 diff, 관련 파일, 테스트 명령, 최대 반복 3회, 비용 예산",
            "steps": ("1회차 Plan/Act/Observe/Evaluate", "2회차 실패 반영 전략 변경", "관련 테스트 재실행", "회귀 문제 확인", "3회차 전체 테스트", "성공 기준 확인", "종료 또는 사람 전달"),
            "tools": "테스트 실행기, diff reader, 실패 signature 저장소, 비용 카운터",
            "human": "3회 반복 후 같은 오류가 남거나 설계 변경이 필요하면 개발자에게 전달합니다.",
            "failure": "동일 실패 signature가 2회 이상 반복되거나 테스트 수가 줄지 않는 경우입니다.",
            "output": "수정 diff, 테스트 결과, 시도별 전략 변경 기록, 종료 사유",
            "why": "핵심은 도구 권한보다 관찰 결과를 보고 다음 전략과 종료를 정하는 것입니다.",
            "without": "하네스만 있으면 안전하게 실행할 수는 있지만, 실패 후 무엇을 바꿀지는 정해주지 않습니다.",
        },
        "code_label": "루프 제어 의사 코드",
        "code": """state = {
    \"goal\": \"targeted tests pass and no regression\",
    \"attempt\": 0,
    \"failures\": [],
    \"cost\": 0,
}

while state[\"attempt\"] < 3 and state[\"cost\"] < 3.0:
    plan = make_plan(state)
    diff = act_edit_code(plan)
    result = observe(run_relevant_tests(diff))
    progress = evaluate_progress(result, state[\"failures\"])

    if result.passed:
        final = observe(run_full_tests())
        if final.passed:
            break

    if progress == \"same_failure\":
        state[\"failures\"].append(result.signature)
        state = replan_with_new_strategy(state)
    elif progress == \"no_progress\":
        escalate_to_human(state, result)
        break

    state[\"attempt\"] += 1
    state[\"cost\"] += result.cost""",
        "code_notes": ("반복문, 현재 상태, 실행 결과 관찰, 진행 여부 평가가 루프의 중심입니다.", "권한 allowlist는 하네스에서 다루고, 여기서는 전략 변경과 종료 조건을 다룹니다.", "동일 실패 감지가 없으면 에이전트가 같은 수정을 반복할 수 있습니다."),
        "compare": (
            ("하네스 엔지니어링", "무엇을 허용할 것인가", "도구·권한·검증", "실행 정책", "안전한 실행", "권한 과다", "실행 경계가 문제면 하네스입니다."),
            ("LangGraph", "상태 흐름을 어디에 저장하고 재개할 것인가", "State, Node, Edge", "워크플로 그래프", "장기 실행", "상태 복잡성", "루프가 여러 단계와 승인으로 커지면 LangGraph를 씁니다."),
            ("프롬프트 엔지니어링", "어떻게 지시할 것인가", "지시문·예시", "프롬프트", "첫 시도 품질", "모호한 지시", "반복 이전에 지시가 문제인지 확인합니다."),
        ),
        "failures": (
            ("무한 반복", "종료 조건과 비용 한도가 없음", "시도 횟수와 비용 증가", "max_attempts, max_cost, stop condition 강제"),
            ("진전 없는 재시도", "동일 실패 signature를 기록하지 않음", "같은 테스트가 같은 이유로 실패", "no-progress detection과 전략 변경"),
            ("과도한 전체 테스트", "관찰 범위가 항상 넓음", "시간이 급증", "관련 테스트 후 전체 테스트 순서로 분리"),
        ),
        "checklist": ("Goal과 성공 기준이 측정 가능한가", "State에 실패 signature와 시도 이력이 남는가", "Observe 단계가 테스트 결과와 로그를 구조화하는가", "Evaluate가 진전/무진전/성공을 구분하는가", "최대 반복 횟수와 비용 한도가 있는가", "사람에게 넘길 조건이 명확한가"),
        "roles": (
            ("기획자", "자동 수정이 멈춰야 하는 업무 기준과 사람 전달 조건을 정합니다."),
            ("디자이너", "시도별 진행, 실패 반복, 사람 전달 상태를 보여주는 흐름을 설계합니다."),
            ("프론트엔드", "실행 로그 타임라인과 retry/stop/escalate 상태를 구현합니다."),
            ("백엔드", "테스트 실행 결과 수집, 실패 signature, 비용 카운터를 구현합니다."),
            ("데이터·AI 엔지니어", "반복 전략별 성공률과 평균 시도 횟수를 평가합니다."),
            ("플랫폼·보안 담당자", "루프가 하네스 한도 안에서만 실행되는지 감시합니다."),
        ),
        "learning": (
            ("읽기 전에", "테스트 자동화, 실패 로그, 에이전트 기본 구조"),
            ("다음 문서", "하네스 엔지니어링, LangGraph"),
            ("빠르게 바뀔 수 있는 부분", "에이전트 런타임의 자동 tool loop, 승인 중단, trace 포맷"),
        ),
    },
    "graph-engineering": {
        "difficulty": "중급~고급",
        "audience": "아키텍트 · 데이터 · 플랫폼 · 백엔드 · 보안 담당자",
        "reading_time": "12분",
        "maturity": "이 사이트의 실무적 분류. 특정 프레임워크가 아님",
        "updated_at": REVIEW_DATE,
        "volatile": "그래프 저장소, 시각화 도구, 계보 표준 적용 방식은 조직마다 다름",
        "related": ("langgraph", "context-engineering", "harness-engineering"),
        "keywords": ("Node", "Edge", "Property", "Lineage", "Impact Analysis"),
        "definition": "업무, 데이터, 권한, 서비스, 의존성과 실행 관계를 노드와 엣지로 모델링하는 설계 방법론입니다.",
        "problem": (
            ("기존 방식", "서비스 의존성, 데이터 흐름, 담당 팀, 정책 문서를 각 시스템에서 따로 관리합니다."),
            ("발생하는 문제", "한 서비스 변경이 어떤 API, DB, 팀, 배포 파이프라인에 영향을 주는지 늦게 발견합니다."),
            ("해결 방식", "서비스, API, 데이터베이스, 저장소, 배포 파이프라인, 팀, 정책을 노드로 두고 관계를 방향성 있는 엣지로 연결합니다."),
            ("해결하지 못하는 부분", "그래프 모델은 실행 런타임이 아닙니다. LangGraph처럼 상태 기반 AI 워크플로를 직접 실행하지 않습니다."),
        ),
        "components": (
            "Node는 서비스, API, 데이터베이스, 저장소, 담당 팀 같은 대상을 나타냅니다. Edge는 호출한다, 데이터를 읽는다, 배포된다, 담당한다 같은 방향 관계를 나타냅니다. 속성은 중요도, 소유자, 환경, 민감도이며, 가중치는 장애 영향도나 호출 빈도를 표현합니다.",
            ("변경 대상 서비스", "직접 의존 탐색", "간접 영향", "데이터 계보", "승인자", "테스트 범위", "위험도"),
        ),
        "use_table": (
            ("시스템 영향도와 데이터 계보를 추적해야 함", "단일 서비스 내부 구조만 보면 충분함", "노드·엣지 타입과 소유자가 정의되어 있는가", "문서화된 아키텍처 표"),
            ("권한과 승인 관계가 업무 흐름에 중요함", "관계가 거의 변하지 않는 작은 프로젝트", "그래프 갱신 책임과 자동 수집 경로가 있는가", "체크리스트"),
            ("변경 전 테스트 범위를 계산해야 함", "모든 변경에 항상 전체 테스트를 실행함", "중요도와 방향성을 모델링할 수 있는가", "CI 매트릭스"),
        ),
        "case": {
            "title": "서비스 변경 시 영향 범위를 분석하는 시스템 의존성 그래프",
            "goal": "서비스 변경이 API, 데이터베이스, 저장소, 배포 파이프라인, 팀, 정책 문서에 미치는 영향을 탐색합니다.",
            "old_problem": "아키텍처 문서가 오래되어 변경 영향도를 경험 많은 담당자에게 물어봐야 합니다.",
            "input": "변경 대상 서비스, 호출 로그, DB 접근 로그, 저장소 정보, 배포 파이프라인, 팀 소유권, 정책 문서",
            "steps": ("변경 대상 선택", "직접 의존 관계 탐색", "간접 영향 탐색", "데이터 변경 영향 분석", "담당 팀과 승인자 확인", "테스트 범위 결정", "배포 위험도 계산", "근거 기록"),
            "tools": "속성 그래프 모델, 영향도 탐색 쿼리, Mermaid 또는 그래프 시각화, 데이터 계보 표준 참고",
            "human": "높은 중요도 엣지나 순환 의존성이 발견되면 아키텍트가 모델을 검토합니다.",
            "failure": "잘못된 관계나 오래된 엣지가 있으면 영향 범위를 과소평가합니다.",
            "output": "영향받는 서비스·DB·팀 목록, 테스트 범위, 승인자, 배포 위험도, 근거 경로",
            "why": "문제는 실행 순서가 아니라 관계와 의존성의 가시화입니다.",
            "without": "LangGraph로 실행 흐름을 만들 수는 있지만 시스템 전체 의존성 모델을 대신하지는 않습니다.",
        },
        "code_label": "그래프 모델링 의사 코드",
        "code": """nodes = [
    Node(\"service\", \"billing-api\", criticality=\"high\"),
    Node(\"api\", \"POST /payments\", pii=True),
    Node(\"database\", \"orders-db\", sensitivity=\"customer\"),
    Node(\"pipeline\", \"billing-prod-deploy\"),
    Node(\"team\", \"payments-platform\"),
    Node(\"policy\", \"payment-data-retention\"),
]

edges = [
    Edge(\"billing-api\", \"POST /payments\", \"exposes\", weight=0.9),
    Edge(\"billing-api\", \"orders-db\", \"writes\", weight=1.0),
    Edge(\"billing-prod-deploy\", \"billing-api\", \"deploys\", weight=0.8),
    Edge(\"payments-platform\", \"billing-api\", \"owns\", weight=1.0),
    Edge(\"orders-db\", \"payment-data-retention\", \"governed_by\", weight=0.7),
]

impact = traverse(start=\"billing-api\", depth=3, include=(\"writes\", \"deploys\", \"owns\", \"governed_by\"))
risk = score_impact(impact, factors=(\"criticality\", \"sensitivity\", \"weight\"))""",
        "code_notes": ("Node와 Edge는 실행 단계가 아니라 관계 모델입니다.", "방향성과 가중치가 있어야 영향도 탐색과 위험도 계산이 가능합니다.", "데이터 계보와 권한 관계는 별도 엣지 타입으로 표현합니다."),
        "compare": (
            ("워크플로 그래프", "업무 단계가 어떻게 흘러가는가", "작업 노드와 전이", "업무 흐름도", "승인 프로세스", "데이터 계보 부족", "실행 순서가 핵심이면 워크플로 그래프"),
            ("지식 그래프", "개념과 사실이 어떻게 연결되는가", "엔티티와 관계", "지식 질의 모델", "검색·추천", "운영 영향도 부족", "질문 답변 근거가 핵심이면 지식 그래프"),
            ("시스템 의존성 그래프", "서비스 변경이 어디에 영향을 주는가", "서비스·DB·팀·정책", "영향도 그래프", "변경·배포", "갱신 비용", "변경 위험 분석이면 의존성 그래프"),
        ),
        "failures": (
            ("그래프가 너무 커짐", "모든 관계를 처음부터 모델링", "탐색 결과가 잡음으로 가득함", "핵심 서비스와 고위험 데이터부터 시작"),
            ("방향성이 빠짐", "관계를 단순 연결로만 저장", "영향도 탐색이 양방향으로 오염", "read/write/calls/owns 등 방향 타입 정의"),
            ("오래된 관계", "자동 수집과 소유자 검토가 없음", "실제 호출 로그와 그래프가 다름", "갱신 주기와 stale edge 표시"),
        ),
        "checklist": ("노드 타입과 엣지 타입이 업무 질문을 답할 수 있게 정의됐는가", "속성, 방향성, 중요도 또는 가중치가 있는가", "데이터 계보와 권한 관계가 구분되는가", "순환 의존성을 찾는 쿼리가 있는가", "그래프 갱신 책임자와 자동 수집 경로가 있는가", "LangGraph와의 차이를 문서에 명시했는가"),
        "roles": (
            ("기획자", "변경 승인과 영향도 보고에 필요한 질문을 정의합니다."),
            ("디자이너", "영향 경로, 위험도, 담당자, 근거를 읽기 쉬운 그래프 UI로 설계합니다."),
            ("프론트엔드", "그래프 탐색, 필터, 경로 하이라이트, 모바일 대체 표를 구현합니다."),
            ("백엔드", "서비스 카탈로그, 로그, CI/CD, 정책 문서에서 그래프 데이터를 수집합니다."),
            ("데이터·AI 엔지니어", "계보와 영향도 점수 모델, 그래프 검색 품질을 관리합니다."),
            ("플랫폼·보안 담당자", "민감 데이터, 권한, 승인자 관계를 최신 상태로 유지합니다."),
        ),
        "learning": (
            ("읽기 전에", "서비스 의존성, 데이터 계보, 그래프 기본 개념"),
            ("다음 문서", "LangGraph, 컨텍스트 엔지니어링"),
            ("빠르게 바뀔 수 있는 부분", "그래프 DB 제품 기능, 시각화 도구, 조직별 메타데이터 표준"),
        ),
    },
}

KNOWLEDGE_PAGES["agent-engineering"] = {
    "difficulty": "중급~고급",
    "audience": "AI 엔지니어 · 백엔드 · 플랫폼 · 제품 책임자",
    "reading_time": "12분",
    "maturity": "실무 운영 관점의 상위 개념",
    "updated_at": REVIEW_DATE,
    "volatile": "에이전트 프레임워크와 관측 도구의 기능은 빠르게 바뀔 수 있음",
    "related": ("harness-engineering", "loop-engineering", "graph-engineering", "langgraph"),
    "keywords": ("Evaluation", "Observability", "Guardrails", "Tool Use", "Human Approval"),
    "definition": "모델, 도구, 데이터, 평가, 관측, 보안을 함께 설계해 AI 에이전트를 실제 업무 환경에서 안정적으로 운영하는 분야입니다.",
    "problem": (
        ("기존 방식", "프롬프트나 데모 품질만 확인한 뒤 에이전트를 바로 업무에 연결합니다."),
        ("발생하는 문제", "비용 증가, 잘못된 도구 실행, 품질 저하, 보안 사고가 배포 후에야 발견됩니다."),
        ("해결 방식", "평가셋, 도구 권한, 승인 절차, 실행 로그, 비용 한도, 장애 대응을 제품 운영 과정에 포함합니다."),
        ("해결하지 못하는 부분", "업무 목표와 책임 범위가 불명확하면 기술만으로 안전한 자동화를 만들 수 없습니다."),
    ),
    "components": (
        "에이전트 엔지니어링은 모델이 판단하고 도구가 실행하는 흐름에 평가와 관측을 붙입니다. 하네스가 권한과 검증의 안전 경계를 제공하고, 루프와 그래프가 작업 흐름을 제어하며, 운영자는 로그와 평가 결과로 품질 변화를 확인합니다.",
        ("업무 목표", "도구·권한 설계", "평가셋", "에이전트 실행", "관측·로그", "승인·복구", "지속 개선"),
    ),
    "use_table": (
        ("AI가 읽기뿐 아니라 업무 도구를 실행함", "답변 생성만 하는 단순 챗봇", "성공 기준과 실패 비용을 정할 수 있는가", "단일 모델 호출과 사람 검토"),
        ("배포 뒤 품질·비용·오류를 계속 추적해야 함", "일회성 분석이나 실험", "평가 데이터와 로그를 보관할 수 있는가", "짧은 프로토타입"),
        ("여러 팀이 같은 에이전트를 운영함", "한 명이 제한된 범위에서만 사용함", "승인자와 책임자가 정해졌는가", "명시적인 수동 절차"),
    ),
    "case": {
        "title": "고객 문의를 분류하고 답변 초안을 만드는 지원 에이전트",
        "goal": "문의 유형을 분류하고 승인 가능한 답변 초안을 만들되, 개인정보와 환불 결정은 사람에게 넘깁니다.",
        "old_problem": "담당자가 반복 문의를 직접 분류하고, 답변 품질이나 처리 시간이 팀마다 달라집니다.",
        "input": "고객 문의, 승인된 도움말, 주문 상태 읽기 권한, 금지 표현 목록, 평가용 문의 세트",
        "steps": ("문의 분류", "관련 도움말 검색", "답변 초안", "정책·개인정보 검사", "신뢰도 평가", "사람 승인 또는 발송", "결과 로그와 평가 갱신"),
        "tools": "검색 도구, 읽기 전용 주문 조회, 정책 검사기, 평가셋, 추적 로그, 승인 화면",
        "human": "환불, 계정 변경, 법률·안전 이슈, 낮은 신뢰도 답변은 담당자가 승인합니다.",
        "failure": "근거 없는 답변, 권한 밖의 주문 조회, 같은 오류의 반복, 응답 지연과 비용 증가입니다.",
        "output": "근거 링크가 있는 답변 초안, 분류 결과, 승인 상태, 품질·비용 지표",
        "why": "좋은 프롬프트만으로는 배포 후 품질 변화와 권한 문제를 관리할 수 없기 때문입니다.",
        "without": "답변 초안은 만들 수 있지만, 누가 무엇을 검토했고 품질이 좋아졌는지 추적하기 어렵습니다.",
    },
    "code_label": "에이전트 운영 흐름 의사 코드",
    "code": '''result = agent.run(ticket, tools=read_only_tools)
checked = policy_check(result, rules=approved_rules)
score = evaluate(checked, dataset=support_eval_set)
trace.record(ticket=ticket.id, result=checked, score=score)

if score.confidence < 0.85 or checked.requires_approval:
    request_human_approval(checked)
else:
    send_draft(checked)

alert_if(metrics.error_rate > 0.03 or metrics.cost_today > budget)''',
    "code_notes": ("실행 뒤에 정책 검사와 평가를 분리하면 문제가 난 지점을 찾기 쉽습니다.", "권한이 큰 도구는 자동 실행 대신 승인 단계에 연결합니다.", "지표 경보는 품질 저하나 비용 급증을 빨리 발견하는 데 사용합니다."),
    "compare": (
        ("하네스 엔지니어링", "실행을 어떻게 안전하게 제한할 것인가", "권한·도구·검증", "안전 경계", "도구 실행", "정책 누락", "실행 경계가 핵심이면 하네스입니다."),
        ("루프 엔지니어링", "실패 뒤 다음 행동을 어떻게 정할 것인가", "반복·평가·종료", "반복 제어", "수정과 재시도", "무한 반복", "반복 전략이 핵심이면 루프입니다."),
        ("그래프 엔지니어링", "관계와 의존성을 어떻게 모델링할 것인가", "노드·엣지·영향도", "관계 모델", "복잡한 시스템", "오래된 관계", "구조 파악이 핵심이면 그래프입니다."),
    ),
    "failures": (
        ("데모 품질만 확인", "대표적이지 않은 예시만 사용", "실사용에서 오류 유형이 급증", "실제 문의와 실패 사례로 평가셋을 유지"),
        ("과도한 권한", "쓰기 도구를 기본 허용", "의도하지 않은 변경 로그", "읽기·쓰기 권한 분리와 사람 승인"),
        ("관측 부재", "실행 결과와 비용을 기록하지 않음", "품질 하락 시점을 알 수 없음", "트레이스·평가·비용 지표와 경보 설정"),
    ),
    "checklist": ("업무 성공 기준과 사람 승인 기준이 있는가", "도구 권한이 최소 범위로 제한되는가", "대표적인 실제 입력으로 평가하는가", "오류·비용·시간을 추적하는가", "품질 저하 시 중단·복구 절차가 있는가", "평가 결과를 다음 개선에 반영하는가"),
    "roles": (
        ("기획자", "자동화 범위, 성공 기준, 사람이 결정할 업무를 정의합니다."),
        ("디자이너", "신뢰도, 근거, 승인 대기, 오류 상태를 이해하기 쉽게 설계합니다."),
        ("프론트엔드", "승인 화면, 실행 이력, 피드백 수집 UI를 구현합니다."),
        ("백엔드", "도구 권한, 정책 검사, 로그 저장, 오류 복구를 구현합니다."),
        ("데이터·AI 엔지니어", "평가셋, 품질 지표, 회귀 테스트를 관리합니다."),
        ("플랫폼·보안 담당자", "비밀정보, 접근 권한, 감사 로그, 비용 한도를 관리합니다."),
    ),
    "learning": (
        ("읽기 전에", "프롬프트, 도구 호출, 권한, 테스트 기본 개념"),
        ("다음 문서", "하네스 엔지니어링, 루프 엔지니어링, 그래프 엔지니어링"),
        ("빠르게 바뀔 수 있는 부분", "에이전트 SDK, 관측·평가 도구, 모델별 도구 호출 방식"),
    ),
}

OFFICIAL_SOURCES["agent-engineering"] = (
    ("OpenAI Agents SDK", "https://openai.github.io/openai-agents-python/"),
    ("LangChain State of Agent Engineering", "https://www.langchain.com/state-of-agent-engineering"),
)


REQUIRED_KNOWLEDGE_METADATA = (
    "id",
    "slug",
    "title",
    "oneLineDefinition",
    "coreQuestion",
    "summary",
    "difficulty",
    "audience",
    "readingTime",
    "maturity",
    "updatedAt",
    "keywords",
    "relatedConcepts",
    "confusingConcepts",
    "officialSources",
    "volatileSections",
    "representativeUseCase",
)


NEW_KNOWLEDGE_DECISION_RULES = (
    ("신규 후보", "독립적인 설계 원칙이나 엔지니어링 방법론이면 신규 Knowledge 후보로 검토합니다."),
    ("기존 하위 기술", "기존 개념의 세부 구현이면 관련 Knowledge의 더 알아보기나 하위 주제로 포함합니다."),
    ("제품·라이브러리", "특정 제품이나 라이브러리는 별도 Knowledge보다 관련 개념의 실제 사례로 우선 다룹니다."),
    ("일시적 트렌드", "마케팅 용어이거나 지속성이 불명확하면 주간 뉴스레터 카드로만 다룹니다."),
    ("중복 방지", "기존 Knowledge와 핵심 질문이 같으면 새 페이지를 만들지 않고 기존 문서를 보강합니다."),
)


_KNOWLEDGE_METADATA = {
    "langchain": {
        "id": "01",
        "title": "LangChain",
        "summary": "LLM 앱을 만들 때 모델 호출, 프롬프트, 도구 연결, 검색, 메모리 같은 부품을 한 흐름으로 묶는 개발 프레임워크입니다.",
        "coreQuestion": "컴포넌트를 어떻게 연결할 것인가",
        "designTarget": "모델, 프롬프트, 검색기, 도구",
        "representativeOutput": "AI 애플리케이션 파이프라인",
        "representativeFailure": "프레임워크 복잡성, 종속성",
        "bestFit": "모델 호출과 외부 기능 연결이 많을 때",
        "relationshipStage": "1. 설계",
        "relationships": ("프롬프트와 컨텍스트를 실행 가능한 앱 구성요소로 연결", "LangGraph로 복잡한 상태 흐름을 확장"),
        "atAGlance": ("Prompt", "Model", "Parser", "Retriever", "Tool"),
        "coreComponents": (
            ("Prompt", "무엇을 요청할지 정합니다.", "회의록에서 결정 사항만 뽑으라고 지시합니다."),
            ("Model", "답을 생성합니다.", "요약과 실행 항목 초안을 만듭니다."),
            ("Parser", "출력을 정해진 형식으로 받습니다.", "담당자, 마감일, 우선순위를 필드로 검증합니다."),
            ("Tool", "외부 시스템과 연결합니다.", "업무 관리 도구에 등록 초안을 보냅니다."),
        ),
        "confusingConcepts": (("LangChain", "LangGraph", "LangChain은 컴포넌트를 연결하고 LangGraph는 상태와 실행 순서를 제어합니다."),),
        "representativeUseCase": {
            "title": "회의록 자동 등록",
            "situation": "회의록을 붙여 넣으면 요약, 실행 항목, 담당자, 마감일을 구조화합니다.",
            "oldProblem": "프롬프트, 모델 호출, 업무 도구 등록 코드가 한 덩어리로 얽힙니다.",
            "process": "입력 템플릿, 구조화 출력, 검색기, 도구 호출을 분리해 연결합니다.",
            "result": "도구나 출력 형식이 바뀌어도 해당 구성요소만 교체해 유지보수합니다.",
            "limit": "프레임워크 추상화가 과하면 작은 기능도 복잡해질 수 있습니다.",
        },
    },
    "langgraph": {
        "id": "02",
        "title": "LangGraph",
        "summary": "AI 에이전트가 여러 단계를 오가며 판단해야 할 때, 작업 흐름을 그래프 구조로 설계하고 제어하는 도구입니다.",
        "coreQuestion": "상태와 분기를 어떻게 실행할 것인가",
        "designTarget": "State, Node, Edge, Checkpoint",
        "representativeOutput": "상태 기반 워크플로",
        "representativeFailure": "상태 설계 오류, 복잡한 흐름",
        "bestFit": "장기 실행, 승인, 재시도가 필요한 작업",
        "relationshipStage": "2. 실행",
        "relationships": ("LangChain 구성요소를 상태 기반 흐름으로 실행", "루프 엔지니어링의 반복 규칙을 구현"),
        "atAGlance": ("State", "Node", "Branch", "Checkpoint", "Resume"),
        "coreComponents": (
            ("State", "현재까지의 정보와 결정을 저장합니다.", "수집한 로그, 가설, 승인 여부를 남깁니다."),
            ("Node", "하나의 작업 단계를 맡습니다.", "로그 조회, 원인 분석, 조치 생성이 각각 노드가 됩니다."),
            ("Branch", "조건에 따라 다음 경로를 고릅니다.", "확신이 낮으면 추가 조회로 보냅니다."),
            ("Checkpoint", "중간 상태를 저장합니다.", "중단 후 같은 지점에서 재개합니다."),
        ),
        "confusingConcepts": (("LangGraph", "그래프 엔지니어링", "LangGraph는 실행 그래프이고 그래프 엔지니어링은 관계와 의존성 모델링입니다."),),
        "representativeUseCase": {
            "title": "장애 원인 분석",
            "situation": "로그 수집, 원인 추정, 추가 조회, 사람 승인, 조치 제안을 여러 단계로 실행합니다.",
            "oldProblem": "한 번에 답을 내면 중간 근거와 재시도 지점을 잃습니다.",
            "process": "작업을 상태가 남는 노드와 조건 분기로 나누고 승인 지점에서 멈춥니다.",
            "result": "실패한 단계만 다시 실행하고 같은 지점에서 이어갈 수 있습니다.",
            "limit": "상태 스키마가 모호하면 분기와 재개가 불안정해집니다.",
        },
    },
    "prompt-engineering": {
        "id": "03",
        "title": "프롬프트엔지니어링",
        "summary": "AI가 원하는 방식으로 답하도록 지시문, 역할, 예시, 출력 형식을 설계하는 방법입니다.",
        "coreQuestion": "무엇을 어떻게 지시할 것인가",
        "designTarget": "역할, 목표, 제약, 출력 형식",
        "representativeOutput": "재사용 가능한 프롬프트",
        "representativeFailure": "모호한 요청, 출력 불안정",
        "bestFit": "답변 기준과 형식을 안정화해야 할 때",
        "relationshipStage": "1. 설계",
        "relationships": ("컨텍스트 엔지니어링이 제공한 판단 재료를 어떻게 사용할지 지시", "하네스의 검증 기준으로 확장"),
        "atAGlance": ("Role", "Goal", "Context", "Constraint", "Output"),
        "coreComponents": (
            ("Role", "AI가 맡을 관점을 정합니다.", "계약 검토 담당자처럼 행동하게 합니다."),
            ("Goal", "최종 산출물을 정합니다.", "위험 조항 5개와 수정안을 요구합니다."),
            ("Constraint", "하지 말아야 할 일을 제한합니다.", "원문에 없는 법적 판단은 쓰지 않게 합니다."),
            ("Output", "답변 형식을 고정합니다.", "조항, 위험, 근거, 제안 컬럼으로 받습니다."),
        ),
        "confusingConcepts": (("프롬프트", "컨텍스트", "프롬프트는 할 일을 지시하고 컨텍스트는 판단 재료를 고릅니다."),),
        "representativeUseCase": {
            "title": "계약 검토 요청",
            "situation": "위험 조항, 근거 문장, 수정 제안을 표로 뽑아야 합니다.",
            "oldProblem": "막연한 검토 요청은 담당자마다 답변 범위와 형식이 흔들립니다.",
            "process": "역할, 판단 기준, 금지 범위, 출력 컬럼을 명시한 업무 지시로 바꿉니다.",
            "result": "답변 품질이 개인 감각이 아니라 재사용 가능한 기준에 가까워집니다.",
            "limit": "원문에 없는 법률 판단이나 최신 규정은 별도 검증이 필요합니다.",
        },
    },
    "context-engineering": {
        "id": "04",
        "title": "컨텍스트엔지니어링",
        "summary": "AI가 답을 만들 때 참고해야 할 문서, 데이터, 대화 이력, 규칙을 알맞게 골라 넣는 설계 방법입니다.",
        "coreQuestion": "어떤 정보를 제공할 것인가",
        "designTarget": "검색 자료, 메모리, 권한, 최신성",
        "representativeOutput": "컨텍스트 구성 파이프라인",
        "representativeFailure": "관련 없는 정보, 오래된 정보",
        "bestFit": "근거와 내부 자료가 답변 품질을 좌우할 때",
        "relationshipStage": "1. 설계",
        "relationships": ("프롬프트가 사용할 판단 재료를 선별", "RAG와 권한 필터링의 기반"),
        "atAGlance": ("Question", "Retrieve", "Filter", "Assemble", "Answer"),
        "coreComponents": (
            ("Retriever", "관련 문서를 찾습니다.", "질문과 가까운 정책 문서를 검색합니다."),
            ("Metadata", "문서의 조건을 확인합니다.", "날짜, 부서, 권한 등으로 거릅니다."),
            ("Rerank", "가장 필요한 근거를 앞에 둡니다.", "핵심 문서를 우선 전달합니다."),
            ("Token Budget", "넣을 정보량을 조절합니다.", "불필요한 긴 문서를 줄입니다."),
        ),
        "confusingConcepts": (("컨텍스트", "하네스", "컨텍스트는 모델이 보는 정보이고 하네스는 실행 경계와 권한입니다."),),
        "representativeUseCase": {
            "title": "사내 정책 챗봇",
            "situation": "사용자 질문에 맞는 최신 정책 문서와 권한이 허용된 내용만 전달합니다.",
            "oldProblem": "문서를 많이 넣으면 오래된 문서나 권한 밖 정보가 답변을 오염시킵니다.",
            "process": "검색, 날짜·부서·권한 필터, 재정렬, 토큰 예산 조절을 거칩니다.",
            "result": "근거가 명확한 최신 답변을 만들고 권한 밖 정보 노출을 줄입니다.",
            "limit": "원본 문서 품질과 메타데이터가 낮으면 검색 품질도 낮아집니다.",
        },
    },
    "harness-engineering": {
        "id": "05",
        "title": "하네스 엔지니어링",
        "summary": "AI 에이전트가 실제 업무 도구를 사용할 때 실행 순서, 권한, 검증, 기록을 한곳에서 관리하는 운영 구조입니다.",
        "coreQuestion": "무엇을 얼마나 안전하게 허용할 것인가",
        "designTarget": "도구, 권한, 샌드박스, 검증, 로그",
        "representativeOutput": "실행 환경과 안전 장치",
        "representativeFailure": "위험한 실행, 감사 불가",
        "bestFit": "AI가 실제 시스템을 읽거나 수정할 때",
        "relationshipStage": "2. 실행",
        "relationships": ("루프가 선택한 행동을 안전한 권한 안에서 실행", "에이전트 엔지니어링의 운영 경계 역할"),
        "atAGlance": ("Tools", "Permissions", "Sandbox", "Validation", "Audit"),
        "coreComponents": (
            ("Tool Registry", "사용 가능한 도구를 제한합니다.", "읽기, 테스트, 배포 도구를 구분합니다."),
            ("Permission", "권한과 승인 기준을 둡니다.", "삭제나 배포는 승인 뒤 실행합니다."),
            ("Sandbox", "실행 범위를 격리합니다.", "작업 디렉터리 밖 변경을 막습니다."),
            ("Audit Log", "행동 근거를 남깁니다.", "누가 어떤 명령을 왜 실행했는지 추적합니다."),
        ),
        "confusingConcepts": (("하네스", "루프", "하네스는 실행 경계를 강제하고 루프는 다음 행동과 종료를 결정합니다."),),
        "representativeUseCase": {
            "title": "코딩 에이전트 운영",
            "situation": "읽을 파일, 수정 범위, 실행 테스트, 승인 필요한 명령을 제한합니다.",
            "oldProblem": "자유 실행을 맡기면 위험한 파일 변경이나 검증 없는 배포가 발생할 수 있습니다.",
            "process": "도구 레지스트리, 권한 정책, 샌드박스, 검증 명령, 감사 로그를 둡니다.",
            "result": "실행 범위와 검증 근거가 남아 운영 중 사고 대응이 쉬워집니다.",
            "limit": "권한 모델이 너무 느슨하면 안전 장치가 우회되고 너무 엄격하면 작업이 막힙니다.",
        },
    },
    "loop-engineering": {
        "id": "06",
        "title": "루프 엔지니어링",
        "summary": "AI가 한 번 답하고 끝나는 것이 아니라 실행, 관찰, 평가, 수정 과정을 반복하며 결과를 개선하도록 설계하는 방법입니다.",
        "coreQuestion": "다음 행동과 종료를 어떻게 결정할 것인가",
        "designTarget": "상태, 반복, 평가, 종료 조건",
        "representativeOutput": "반복 제어 정책",
        "representativeFailure": "무한 반복, 진전 없는 재시도",
        "bestFit": "실패 결과를 보고 전략을 바꿔야 할 때",
        "relationshipStage": "2. 실행",
        "relationships": ("LangGraph로 구현될 수 있는 반복 판단 규칙", "하네스가 제공한 실행 결과를 평가"),
        "atAGlance": ("Plan", "Act", "Observe", "Evaluate", "Stop"),
        "coreComponents": (
            ("Plan", "다음 시도를 정합니다.", "어떤 테스트부터 볼지 고릅니다."),
            ("Act", "작업을 실행합니다.", "코드를 수정하거나 명령을 실행합니다."),
            ("Observe", "결과를 읽습니다.", "실패 로그와 변경 결과를 확인합니다."),
            ("Evaluate", "진전 여부를 판단합니다.", "같은 실패가 반복되는지 봅니다."),
            ("Stop", "종료 조건을 둡니다.", "통과, 승인 필요, 반복 실패에서 멈춥니다."),
        ),
        "confusingConcepts": (("루프", "하네스", "루프는 반복 판단이고 하네스는 실제 실행을 제한하는 환경입니다."),),
        "representativeUseCase": {
            "title": "테스트 실패 자동 수정",
            "situation": "테스트 실패를 읽고 코드를 고친 뒤 다시 테스트하며 멈출 조건을 확인합니다.",
            "oldProblem": "한 번 실행하고 끝나면 실패 로그를 다음 행동에 활용하지 못합니다.",
            "process": "계획, 실행, 관찰, 평가, 종료 조건을 명시한 반복 흐름을 둡니다.",
            "result": "같은 실패를 반복하거나 무한 재시도하는 대신 진전 여부를 기준으로 멈춥니다.",
            "limit": "평가 기준이 약하면 잘못된 방향으로 여러 번 반복할 수 있습니다.",
        },
    },
    "graph-engineering": {
        "id": "07",
        "title": "그래프 엔지니어링",
        "summary": "AI 업무 흐름, 지식, 권한, 도구 의존성을 노드와 엣지로 표현해 복잡한 에이전트 시스템을 제어하는 설계 방법입니다.",
        "coreQuestion": "관계와 의존성을 어떻게 모델링할 것인가",
        "designTarget": "노드, 엣지, 속성, 계보",
        "representativeOutput": "관계 모델과 영향도 그래프",
        "representativeFailure": "지나치게 큰 그래프, 잘못된 관계",
        "bestFit": "업무·데이터·권한의 의존성을 추적할 때",
        "relationshipStage": "3. 운영",
        "relationships": ("컨텍스트의 출처와 권한 관계를 구조화", "에이전트 운영에서 영향도와 감사 경로를 제공"),
        "atAGlance": ("Node", "Edge", "Property", "Direction", "Impact"),
        "coreComponents": (
            ("Node", "대상을 표현합니다.", "서비스, DB, API, 팀을 하나의 점으로 둡니다."),
            ("Edge", "관계를 표현합니다.", "호출한다, 소유한다, 배포한다를 선으로 잇습니다."),
            ("Property", "관계의 속성을 붙입니다.", "중요도, 변경 빈도, 소유자를 기록합니다."),
            ("Direction", "영향 방향을 정합니다.", "API 변경이 어떤 소비자에게 전파되는지 봅니다."),
        ),
        "confusingConcepts": (("그래프 엔지니어링", "LangGraph", "그래프 엔지니어링은 관계 모델링이고 LangGraph는 AI 실행 흐름 도구입니다."),),
        "representativeUseCase": {
            "title": "결제 API 변경 영향 분석",
            "situation": "결제 API, 주문 DB, 정산 서비스, 알림, 배포 파이프라인의 연결을 따라 영향 범위를 봅니다.",
            "oldProblem": "목록형 문서만 있으면 간접 의존성과 담당자를 놓치기 쉽습니다.",
            "process": "서비스, DB, 팀, 정책을 노드로 두고 호출·소유·배포 관계를 엣지로 연결합니다.",
            "result": "변경 전에 어떤 서비스와 데이터가 같이 흔들리는지 빠르게 확인합니다.",
            "limit": "그래프가 최신 호출 로그와 소유권 정보를 반영하지 않으면 오판합니다.",
        },
    },
    "agent-engineering": {
        "id": "08",
        "title": "에이전트 엔지니어링",
        "summary": "모델, 도구, 데이터, 평가, 관측, 보안을 함께 설계해 AI 에이전트를 실제 업무 환경에서 안정적으로 운영하는 분야입니다.",
        "coreQuestion": "AI 에이전트를 어떻게 안정적으로 운영할 것인가",
        "designTarget": "모델, 도구, 평가, 관측, 보안",
        "representativeOutput": "운영 기준과 안전 지침",
        "representativeFailure": "품질 저하, 비용 증가, 권한 과다",
        "bestFit": "AI가 실제 업무 도구를 실행하고 여러 사람이 함께 운영할 때",
        "relationshipStage": "3. 운영",
        "relationships": ("하네스, 루프, 그래프를 포함하는 상위 운영 관점", "평가와 관측으로 배포 후 품질을 관리"),
        "atAGlance": ("Goal", "Tools", "Evaluation", "Observability", "Approval"),
        "coreComponents": (
            ("Goal", "업무 성공 기준을 정합니다.", "문의 처리 정확도와 승인 기준을 수치로 둡니다."),
            ("Tools", "에이전트가 사용할 기능을 제한합니다.", "주문 조회는 읽기 전용으로 둡니다."),
            ("Evaluation", "실제 입력으로 품질을 검증합니다.", "대표 문의 세트로 회귀를 확인합니다."),
            ("Observability", "실행 상태를 기록합니다.", "오류, 비용, 지연, 도구 호출을 추적합니다."),
            ("Approval", "위험한 결정을 사람이 확인합니다.", "환불이나 계정 변경은 승인 뒤 처리합니다."),
        ),
        "confusingConcepts": (("에이전트 엔지니어링", "하네스 엔지니어링", "에이전트 엔지니어링은 운영 전체이고 하네스는 실행 경계와 권한에 집중합니다."),),
        "representativeUseCase": {
            "title": "고객 지원 에이전트 운영",
            "situation": "고객 문의를 분류하고 근거 링크가 있는 답변 초안을 만듭니다.",
            "oldProblem": "데모는 잘 보여도 배포 뒤 품질, 비용, 권한, 승인 책임이 관리되지 않습니다.",
            "process": "평가셋, 읽기 전용 도구, 정책 검사, 승인 화면, 추적 로그를 함께 설계합니다.",
            "result": "답변 품질과 비용 변화를 운영 지표로 보고 위험 결정은 사람에게 넘깁니다.",
            "limit": "업무 목표와 책임자가 불명확하면 기술 장치만으로 안정성을 보장할 수 없습니다.",
        },
    },
}


def _apply_knowledge_metadata() -> None:
    for slug, metadata in _KNOWLEDGE_METADATA.items():
        page = KNOWLEDGE_PAGES[slug]
        page.update(metadata)
        page["slug"] = slug
        page["oneLineDefinition"] = page["definition"]
        page["readingTime"] = page["reading_time"]
        page["updatedAt"] = page["updated_at"]
        page["relatedConcepts"] = tuple(page["related"])
        page["officialSources"] = tuple(OFFICIAL_SOURCES.get(slug, ()))
        page["volatileSections"] = (page["volatile"],)


def validate_knowledge_pages() -> tuple[str, ...]:
    errors: list[str] = []
    known_slugs = set(KNOWLEDGE_PAGES)
    seen_definitions: dict[str, str] = {}
    seen_cases: dict[str, str] = {}
    seen_code: dict[str, str] = {}

    for slug, page in KNOWLEDGE_PAGES.items():
        missing = [field for field in REQUIRED_KNOWLEDGE_METADATA if not page.get(field)]
        if missing:
            errors.append(f"{slug}: missing required metadata {', '.join(missing)}")

        components = tuple(page.get("coreComponents", ()))
        if not 3 <= len(components) <= 5:
            errors.append(f"{slug}: coreComponents must contain 3 to 5 items")

        case = page.get("representativeUseCase")
        if not isinstance(case, dict):
            errors.append(f"{slug}: representativeUseCase must be a dict")
        else:
            case_missing = [
                field
                for field in ("title", "situation", "oldProblem", "process", "result", "limit")
                if not case.get(field)
            ]
            if case_missing:
                errors.append(f"{slug}: representativeUseCase missing {', '.join(case_missing)}")

        for related_slug in tuple(page.get("relatedConcepts", ())):
            if related_slug not in known_slugs:
                errors.append(f"{slug}: unknown relatedConcept {related_slug}")

        definition = str(page.get("oneLineDefinition", "")).strip()
        if definition in seen_definitions:
            errors.append(f"{slug}: duplicate oneLineDefinition with {seen_definitions[definition]}")
        elif definition:
            seen_definitions[definition] = slug

        case_title = str(case.get("title", "")).strip() if isinstance(case, dict) else ""
        if case_title in seen_cases:
            errors.append(f"{slug}: duplicate representativeUseCase title with {seen_cases[case_title]}")
        elif case_title:
            seen_cases[case_title] = slug

        code = str(page.get("code", "")).strip()
        if code in seen_code:
            errors.append(f"{slug}: duplicate code example with {seen_code[code]}")
        elif code:
            seen_code[code] = slug

    return tuple(errors)


_apply_knowledge_metadata()
