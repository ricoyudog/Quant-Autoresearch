from memory.iteration_artifacts import render_experiment_note_draft


def test_render_experiment_note_draft_marks_file_as_derived_and_non_final():
    record = {
        "run_id": "run-001",
        "iteration_number": 1,
        "artifact_status": "simulated",
        "execution_mode": "dry_run",
        "summary": {
            "hypothesis": "Test a tighter no-trade band.",
            "strategy_change_summary": "No live strategy change; dry-run artifact bundle only.",
        },
        "decision": {
            "decision": "pending_evaluation",
            "reasons": ["no_live_evaluator_output"],
            "validation_status": "candidate",
            "bounded_result": {},
            "unrestricted_result": {},
            "turnover_fee_lesson": "TODO: evaluate fee impact after a live run.",
        },
        "continuation_context": {
            "manifest_path": "experiments/continuation/current_research_base.json",
            "current_baseline": {
                "title": "Experiment - Minimum Hold Duration v1",
                "raw_note_path": "vault/experiments/minimum-hold.md",
            },
            "next_recommended_experiment": "Test momentum-strength threshold.",
        },
        "artifact_paths": {
            "iteration_record": "experiments/iterations/run-001/iteration-0001/iteration_record.json",
            "context_json": "experiments/iterations/run-001/iteration-0001/context.json",
            "claude_prompt": "experiments/iterations/run-001/iteration-0001/claude_prompt.md",
            "decision": "experiments/iterations/run-001/iteration-0001/decision.json",
        },
    }

    draft = render_experiment_note_draft(record)

    assert "note_type: experiment_draft" in draft
    assert "derived_iteration_artifact" in draft
    assert "not raw evidence" in draft.lower()
    assert "pending_explicit_finalize" in draft
    assert "dry-run / simulated mode" in draft
    assert "Validation status: `candidate`" in draft
    assert "Current baseline: Experiment - Minimum Hold Duration v1" in draft
