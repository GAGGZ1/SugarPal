from datetime import datetime

class BloodSugarReading:
    def __init__(self,value,timestamp=None):
        self.value=value
        self.timestamp=timestamp or datetime.now()

class Meal:
    def __init__(self,food_items,calories,insulin_required,timestamp=None):
        self.food_items=food_items
        self.calories=calories
        self.insulin_required=insulin_required
        self.timestamp=timestamp or datetime.now()

class Exercise:
    def __init__(self,activity,duration,impact,timestamp=None):
        self.activity=activity
        self.duration=duration
        self.impact=impact
        self.timestamp=timestamp or datetime.now()
class User:
    def __init__(self,name,age,contact_info):
        self.name=name
        self.age=age
        self.contact_info=contact_info
