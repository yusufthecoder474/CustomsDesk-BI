"""Validated synthetic-distribution settings; never calibrated to real trade data."""
from pydantic import BaseModel,Field,model_validator

class GeneratorConfig(BaseModel):
    missing_classification_rate: float=Field(default=.05,ge=0,le=1)
    review_rate: float=Field(default=.08,ge=0,le=1)
    status_probabilities: list[float]=[.12,.13,.2,.55]
    priority_probabilities: list[float]=[.2,.6,.2]
    max_response_hours: int=Field(default=96,ge=1,le=240)
    @model_validator(mode='after')
    def probabilities(self):
        for name,size in [('status_probabilities',4),('priority_probabilities',3)]:
            p=getattr(self,name)
            if len(p)!=size or any(v<0 or v>1 for v in p) or abs(sum(p)-1)>1e-9:
                raise ValueError(name+' must have the right number of nonnegative probabilities summing to one')
        return self
