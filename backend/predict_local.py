import json
P = json.load(open("package/model_params.json"))
x = [2000, 150, 250]
print(round(P["intercept"] + sum(c * v for c, v in zip(P["coef"], x)), 2))
