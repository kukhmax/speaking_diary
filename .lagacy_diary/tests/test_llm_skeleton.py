from services.llm import LLM, DummyLLM, get_llm


def test_dummy_llm_generate_contains_prompt_and_context():
    prompt = "Привет, мир!"
    context = "Контекст дневника"

    llm: LLM = DummyLLM()
    out = llm.generate(prompt, context)

    assert "dummy reply" in out
    assert prompt in out
    assert context in out


def test_get_llm_factory_dummy():
    llm = get_llm("dummy")
    assert isinstance(llm, DummyLLM)