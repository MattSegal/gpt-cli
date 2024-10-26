class ClaudeModel:
    Sonnet = "claude-3-5-sonnet-20241022"
    Haiku = "claude-3-haiku-20240307"


MODEL_NAME = "Claude"
DEFAULT_MODEL_OPTION = "sonnet"
MODEL_OPTIONS = {
    "sonnet": ClaudeModel.Sonnet,
    "haiku": ClaudeModel.Haiku,
}
