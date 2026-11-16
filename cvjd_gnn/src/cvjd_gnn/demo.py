"""Small, visibly synthetic fixtures. Never use their metrics as research results."""

from pathlib import Path

from .data import DataError, Dataset, Document, Pair, assign_splits, save_dataset, validate, write_json


def make_demo(output: Path, cvs: int = 60, seed: int = 42) -> dict:
    if cvs < 12:
        raise DataError("Demo can it nhat 12 CV de thu ca ba tap")
    roles = [
        ("backend", "Backend Intern", ("python", "django", "postgresql", "git")),
        ("frontend", "Frontend Intern", ("javascript", "react", "html", "css")),
        ("analytics", "Data Analyst Intern", ("sql", "pandas", "numpy", "power bi")),
    ]
    jobs = {key: Document(key, f"SYNTHETIC DEMO JOB. {title}. Student project work using " + ", ".join(skills),
                          tuple(sorted(skills)), title, "synthetic_demo: not a real posting")
            for key, title, skills in roles}
    documents = {}
    for i in range(cvs):
        primary, secondary = roles[i % 3], roles[(i + 1) % 3]
        selected = tuple(sorted(set(primary[2]) | set(secondary[2][:2])))
        key = f"DEMO_CV_{i:04d}"
        text = (f"SYNTHETIC DEMO ONLY. Fictional student {key}. Academic project {i + 101}. "
                f"Portfolio focus {primary[1]}. Skills: {', '.join(selected)}. University practice project.")
        documents[key] = Document(key, text, selected, source="synthetic_demo: not a real person")
    splits = assign_splits({key: {"cv_text": d.text} for key, d in documents.items()}, seed)
    pairs = []
    for cv in documents.values():
        for jd in jobs.values():
            overlap = len(set(cv.skills).intersection(jd.skills)) / len(jd.skills)
            label = 0 if overlap < 0.4 else 1 if overlap < 0.6 else 2
            pairs.append(Pair(cv.id, jd.id, label, "synthetic", splits[cv.id]))
    dataset = Dataset(documents, jobs, pairs, {"dataset_kind": "synthetic_demo", "seed": seed,
                                              "purpose": "Pipeline tests only. No real people or jobs. No research claims."})
    save_dataset(dataset, output)
    write_json(output / "sample_cv.json", {
        "cv_text": "SYNTHETIC DEMO CV. Student with a Django project using Python, SQL and Git.",
        "cv_skills": ["Python", "Django", "SQL", "Git"],
    })
    return validate(dataset)
