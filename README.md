# Restaurant Chatbot

Restaurant Chatbot is a Python-based task-oriented dialogue system that helps users find restaurants in Cambridge, UK. It integrates natural language understanding, dialogue management, and natural language generation to support interactive restaurant recommendations.

## How to run the system

Python 3.10 is required.

To setup a python environment, install anaconda, navigate to the projects directory and execute

```
conda create --name ds python=3.10
conda activate ds
pip install -r requirements.txt
```

During development we will add dependencies to get these, simply re-run
```
pip install -r requirements.txt
```


To run the system, execute `DialogueAgent.py`:

```
python DialogueAgent.py
```

By default, you will be able to interact through the text console. There are other options which you can check by using the `-h` option.

You can end the dialogue by saying 'bye'.

## Speech interaction

If you want to interact through speech, this can easily be done through [Microsoft Cognitive Services](https://azure.microsoft.com/en-us/products/ai-foundry/tools/speech). You will need to install the additional requirements in `requirements-ms.txt` and modify the files `speechsynthesis/synthesisers.py` and `speechrecognition/recognizers.py` by adding your personal token.


## Unittests

Unittests can be run like this:
### ALL Tests
- python -m unittest discover -p "*_test.py"


### Language Understanding
- python -m unittest languageunderstanding/understandingunits_test.py

### Dialogue Management
- python -m unittest dialoguemanagement/dialoguedecision_test.py
- python -m unittest dialoguemanagement/stateupdate_test.py

### Language Generation
- python -m unittest languagegeneration/generators_test.py 

## Data Attribution

This project uses adapted Cambridge restaurant data and ontology resources. See [DATA_ATTRIBUTION.md](DATA_ATTRIBUTION.md) for dataset sources, licenses, and attribution.