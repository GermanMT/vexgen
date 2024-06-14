from typing import Any

from regex import findall, search


async def cs_is_imported(file_path: str, namespace: str) -> Any:
    with open(file_path, encoding="utf-8") as file:
        try:
            code = file.read()
            return search(rf"using\s+{namespace};", code)
        except Exception as _:
            return False


async def cs_get_used_artifacts(filename: str, namespace: str, cve_description: str) -> list[dict[str, list[int]]]:
    with open(filename, encoding="utf-8") as file:
        code = file.read()
        current_line = 1
        used_artifacts = await get_child_artifacts(namespace, code, cve_description)
        for line in code.split("\n"):
            if not search(r"using\s", line):
                for artifact in used_artifacts:
                    if artifact in line:
                        used_artifacts.setdefault(artifact, []).append(current_line)
            current_line += 1
        for artifact in list(used_artifacts.keys()):
            if not used_artifacts[artifact]:
                del used_artifacts[artifact]
        result = []
        for artifact_name, used_in_lines in used_artifacts.items():
            result.append({
                "artifact_name": artifact_name,
                "used_in_lines": used_in_lines
            })
        return result


async def get_child_artifacts(parent: str, code: str, cve_description: str) -> dict[str, list[int]]:
    used_artifacts: dict[str, list[int]] = {}
    for _ in findall(rf"{parent}\.[^\(\)\s:;]+", code):
        for artifact in _.split(".")[1:]:
            if artifact.lower() in cve_description.lower():
                used_artifacts.setdefault(artifact.strip(), [])
    for _ in findall(rf"using\s+{parent}\s*;\s*{{[^}}]+}}", code):
        for artifact in _.split("{")[1].split("}")[0].split(","):
            if artifact.lower().strip() in cve_description.lower():
                used_artifacts.setdefault(artifact.strip(), [])
    aux = {}
    for artifact in used_artifacts:
        aux.update(await get_child_artifacts(artifact, code, cve_description))
    used_artifacts.update(aux)
    return used_artifacts