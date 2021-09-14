from summarizer import Summarizer
from transformers import Pipeline
from transformers.pipelines import pipeline
from utils import read_pdf
import os
from transformers import T5ForConditionalGeneration, T5Tokenizer

FILE_NAME = os.path.join(os.getcwd(), 'downloads/healthterms.pdf')

def summarize_text(text):
    body = text
    # body = '''
    # Insurance is a means of protection from financial loss. It is a form of risk management, primarily used to hedge against the risk of a contingent or uncertain loss.
    # An entity which provides insurance is known as an insurer, an insurance company, an insurance carrier or an underwriter. A person or entity who buys insurance is known as an insured or as a policyholder. The insurance transaction involves the insured assuming a guaranteed and known - relatively small - loss in the form of payment to the insurer in exchange for the insurer's promise to compensate the insured in the event of a covered loss. The loss may or may not be financial, but it must be reducible to financial terms, and usually involves something in which the insured has an insurable interest established by ownership, possession, or pre-existing relationship.
    # The insured receives a contract, called the insurance policy, which details the conditions and circumstances under which the insurer will compensate the insured. The amount of money charged by the insurer to the policyholder for the coverage set forth in the insurance policy is called the premium. If the insured experiences a loss which is potentially covered by the insurance policy, the insured submits a claim to the insurer for processing by a claims adjuster. A mandatory out-of-pocket expense required by an insurance policy before an insurer will pay a claim is called a deductible (or if required by a health insurance policy, a copayment). The insurer may hedge its own risk by taking out reinsurance, whereby another insurance company agrees to carry some of the risks, especially if the primary insurer deems the risk too large for it to carry.
    # '''
    # model = Summarizer()
    result = model(body, min_length=100)
    return result
    # result1 = model(body, ratio=0.2)  # Specified with ratio
    # # print(result1)
    # result2 = model(body, num_sentences=3)  # Will return 3 sentences 
    # print(result2)


def summarize_text1(text):
    body = text 
    summarizer = pipeline('summarization', model='bart-large-cnn', tokenizer='bart-large-cnn')
    summarizer(body, max_length=512, min_length=30, do_sample=False)


def summarize_text2(text):
    model = T5ForConditionalGeneration.from_pretrained("t5-base")
    tokenizer = T5Tokenizer.from_pretrained("t5-base")
    inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(
        inputs, 
        max_length=len(text)/10, 
        min_length=150, 
        length_penalty=2.0, 
        num_beams=4, 
        early_stopping=True)
    return tokenizer.decode(outputs[0])


def test():
    text = read_pdf(FILE_NAME)
    # result1 = summarize_text(text)
    # print(result1)
    result2 = summarize_text2(text)
    print("********")
    print(result2)

# test()
