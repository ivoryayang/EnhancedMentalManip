## To Run The Experiments
### 1. Environment Setup
We recommend installing the following packages and versions before running the code:

| Packages              | Version |
|-----------------------|---------|
| Pytorch               | 2.1.2   |
| Transformers          | 4.36.2  |
| Tokenizers            | 0.15.0  |
| Openai                | 1.6.1   |
| Scipy                 | 1.11.4  |
| Seaborn               | 0.12.2  |
| Sentence-transformers | 2.3.0   |
| tqdm                  | 4.65.0  |
| Pandas                | 2.1.4   |
| scikit-learn          | 1.2.2   |
| peft                  | 0.7.1   |
| trl                   | 0.7.7   |

If you use conda to manage environment, you can add these channels to ensure you can download the above packages.
```bash
$ conda config --add channels conda-forge pytorch nvidia
```

### 2. Command lines
We provide example command lines in [runfile1](./manipulation_detection/run.sh) and [runfile2](./technique_vulnerability/run.sh) files for running the binary detection and multi-label classification tasks. 

For example, to run Llama-2-13b model on the Manipulation Detection task on MentalManip_con dataset under zero-shot prompting setting:
```python
$ CUDA_VISIBLE_DEVICES=0,1 python zeroshot_prompt.py --model llama-13b \
                          --data ../datasets/mentalmanip_con.csv \
                          --log_dir ./logs
```

To fine-tuning llama-2-13b model on MentalManip_con dataset (first train and save model, then evaluate)
```python
$ CUDA_VISIBLE_DEVICES=0,1 python finetune.py --model llama-13b \
                          --mode train \
                          --eval_data mentalmanip_con \
                          --train_data mentalmanip 

$ CUDA_VISIBLE_DEVICES=0,1 python finetune.py --model llama-13b \
                          --mode eval \
                          --eval_data mentalmanip_con \
                          --train_data mentalmanip 
```

### Important Notes
1. Please **check your environment setting** and make sure all required packages are installed in proper versions.
2. Before running ChatGPT, please place your own api key in the code. You can find your key [here](https://platform.openai.com/settings/profile?tab=api-keys).
3. Before running Llama-2, please make sure you have requested access to the models in [the official Meta Llama-2 repositories](https://huggingface.co/meta-llama).
