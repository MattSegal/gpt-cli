from .prompt import get_client


def get_image_url(prompt: str) -> str:
    client = get_client()
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        style="vivid",
        size="1792x1024",
        quality="hd",
        n=1,
    )
    return response.data[0].url
