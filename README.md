# SE373-IELTS-Learning-Agent
Kho lưu trữ để build website Agentic AI hoàn chỉnh

## Member 1 handoff

See [Member 1 to Member 2 handoff](docs/member1_to_member2_handoff.md) for installation, data generation and retrieval integration.

## Member 2 retrieval and skill

See [Member 2 handoff](docs/member2_handoff.md) for the retrieval tool, Writing
skill, test/evaluation commands and the remaining Member 3/4 integration steps.
See [RAG and skill report](docs/member2_rag_skill_report.md) for design and demo.

After rebuilding the Member 1 index, run from the repository root:

```powershell
.venv/Scripts/python.exe -B -m unittest discover -s tests -v
.venv/Scripts/python.exe -B -m evals.retrieval_eval
.venv/Scripts/python.exe -B -m scripts.demo_retrieval
```

The retriever does not need an LLM API key. The first real embedding call may
download the Chroma ONNX model. The skill delegates validation to Member 4;
Member 3's actual Pydantic model remains the schema authority.
