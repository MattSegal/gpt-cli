class ClaudeModel:
    Sonnet = "claude-3-5-sonnet-latest"
    Haiku = "claude-3-5-haiku-20241022"


MODEL_NAME = "Claude"
DEFAULT_MODEL_OPTION = "haiku"
MODEL_OPTIONS = {
    "sonnet": ClaudeModel.Sonnet,
    "haiku": ClaudeModel.Haiku,
}
