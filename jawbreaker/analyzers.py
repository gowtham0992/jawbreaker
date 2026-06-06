from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from jawbreaker.contract import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from jawbreaker.schema import ScamAnalysis


Prediction = dict[str, Any]
Analyzer = Callable[[str], Prediction]


def analysis_to_prediction(analysis: ScamAnalysis) -> Prediction:
    return {
        "risk_level": analysis.risk_level,
        "scam_type": analysis.scam_type,
        "summary": analysis.summary,
        "tactics": analysis.tactics,
        "safest_action": analysis.safest_action,
        "trusted_person_message": analysis.trusted_person_message,
        "scam_dna": {
            "impersonates": analysis.scam_dna.get("Impersonates", ""),
            "pressure": analysis.scam_dna.get("Pressure", ""),
            "ask": analysis.scam_dna.get("Ask", ""),
            "risk": analysis.scam_dna.get("Risk", ""),
        },
    }


def prediction_to_analysis(prediction: Prediction, *, similar_memory: str = "") -> ScamAnalysis:
    risk_level = prediction.get("risk_level")
    if risk_level not in {"dangerous", "suspicious", "needs_check", "safe"}:
        risk_level = "needs_check"

    tactics = prediction.get("tactics", [])
    if not isinstance(tactics, list):
        tactics = []

    scam_dna = prediction.get("scam_dna", {})
    if not isinstance(scam_dna, dict):
        scam_dna = {}

    return ScamAnalysis(
        risk_level=str(risk_level),
        scam_type=str(prediction.get("scam_type", "unknown")),
        summary=str(prediction.get("summary", "This message should be checked before anyone acts.")),
        tactics=[str(tactic) for tactic in tactics],
        safest_action=str(
            prediction.get(
                "safest_action",
                "Do not click links or reply. Verify through an official app, website, or known phone number.",
            )
        ),
        trusted_person_message=str(
            prediction.get(
                "trusted_person_message",
                "Can you check this for me before I respond or click anything?",
            )
        ),
        scam_dna={
            "Impersonates": str(scam_dna.get("impersonates", "")),
            "Pressure": str(scam_dna.get("pressure", "")),
            "Ask": str(scam_dna.get("ask", "")),
            "Risk": str(scam_dna.get("risk", "")),
        },
        similar_memory=similar_memory,
    )


def heuristic_analyzer(message: str) -> Prediction:
    return analysis_to_prediction(ScamAnalysis.from_heuristics(message))


def load_prediction_jsonl(path: Path) -> dict[str, Prediction]:
    predictions: dict[str, Prediction] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        case_id = row.get("id")
        prediction = row.get("prediction")
        if not isinstance(case_id, str) or not isinstance(prediction, dict):
            raise ValueError(f"{path}:{line_number}: expected fields 'id' and object 'prediction'")
        predictions[case_id] = prediction
    return predictions


def prediction_file_analyzer(predictions: dict[str, Prediction], case_id: str) -> Prediction:
    if case_id not in predictions:
        raise KeyError(f"Missing prediction for case id: {case_id}")
    return predictions[case_id]


def load_json_prediction(content: str) -> Prediction:
    try:
        prediction = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        prediction = json.loads(content[start : end + 1])
    if not isinstance(prediction, dict):
        raise ValueError("model response must be a JSON object")
    return prediction


def build_llama_cpp_analyzer(
    model_path: Path,
    *,
    chat_format: str | None = None,
    n_ctx: int = 4096,
    n_threads: int | None = None,
    n_gpu_layers: int = 0,
    n_batch: int = 512,
    n_ubatch: int = 512,
    offload_kqv: bool = True,
    op_offload: bool | None = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> Analyzer:
    try:
        from llama_cpp import Llama
    except ImportError as exc:
        raise SystemExit(
            "llama-cpp-python is not installed. Install it before running --backend llama-cpp."
        ) from exc

    kwargs: dict[str, Any] = {
        "model_path": str(model_path),
        "n_ctx": n_ctx,
        "n_gpu_layers": n_gpu_layers,
        "n_batch": n_batch,
        "n_ubatch": n_ubatch,
        "offload_kqv": offload_kqv,
        "verbose": False,
    }
    if op_offload is not None:
        kwargs["op_offload"] = op_offload
    if chat_format:
        kwargs["chat_format"] = chat_format
    if n_threads is not None:
        kwargs["n_threads"] = n_threads

    llm = Llama(**kwargs)

    def analyze(message: str) -> Prediction:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(message=message)},
            ],
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response["choices"][0]["message"]["content"]
        return load_json_prediction(content)

    return analyze


def build_transformers_analyzer(
    model_id: str,
    *,
    max_new_tokens: int = 192,
    temperature: float = 0.0,
    device_map: str = "auto",
    dtype: str = "auto",
) -> Analyzer:
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise SystemExit(
            "torch and transformers are required for --backend transformers / ZeroGPU."
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype, device_map=device_map)
    model.eval()

    def analyze(message: str) -> Prediction:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(message=message)},
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": temperature > 0,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if temperature > 0:
            generation_kwargs["temperature"] = temperature
        with torch.inference_mode():
            output_ids = model.generate(**inputs, **generation_kwargs)
        new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
        content = tokenizer.decode(new_tokens, skip_special_tokens=True)
        return load_json_prediction(content)

    return analyze


def validate_prediction(prediction: Prediction) -> list[str]:
    errors = []
    required = {
        "risk_level",
        "scam_type",
        "summary",
        "tactics",
        "safest_action",
        "trusted_person_message",
        "scam_dna",
    }
    missing = required - set(prediction)
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
    if prediction.get("risk_level") not in {"dangerous", "suspicious", "needs_check", "safe"}:
        errors.append(f"invalid risk_level: {prediction.get('risk_level')}")
    if not isinstance(prediction.get("tactics"), list):
        errors.append("tactics must be a list")
    if not isinstance(prediction.get("scam_dna"), dict):
        errors.append("scam_dna must be an object")
    for key in ["scam_type", "summary", "safest_action", "trusted_person_message"]:
        if key in prediction and not isinstance(prediction[key], str):
            errors.append(f"{key} must be a string")
    return errors


def write_predictions(path: Path, rows: Iterable[dict], predictions: dict[str, Prediction]) -> None:
    lines = []
    for row in rows:
        case_id = row["id"]
        lines.append(json.dumps({"id": case_id, "prediction": predictions[case_id]}, ensure_ascii=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
