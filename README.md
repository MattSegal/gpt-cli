# Teeny Tiny GPT-4 CLI Wrapper

```
$ gpt what is eigenvector decompisition


    Eigenvector decomposition is a method of breaking down a square matrix into its constituent parts.
    The concept is crucial in areas of linear algebra and fields such as facial recognition and
    machine learning algorithms.

    The decomposition is based on the Eigenvalues (the factors by which an associated eigenvector is
    scaled) and eigenvectors (the non-zero vectors which remain in the same direction even after
    linear transformation).

    If 'A' is a square matrix, then the decomposition provides:

    A = PDP^-1

    where
    - 'P' is a matrix whose columns are the eigenvectors of 'A'
    - 'D' is a diagonal matrix whose entries are the eigenvalues of 'A'
    - P^-1 is the inverse matrix of 'P'

    This demonstrates that any matrix that can be eigendecomposed represents a map that stretches
    space along its eigenvectors.

```

## Local setup

```bash
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

.bashrc:

```bash
export OPENAI_KEY="sk-XXXXXXXX"
export GPT_HOME="/home/myname/code/gpt
. $GPT_HOME/funcs.sh
```
