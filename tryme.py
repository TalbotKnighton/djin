from math import cos

from pydantic import BaseModel, ImportString, ValidationError


class ImportThings(BaseModel):
    obj: ImportString


# A string value will cause an automatic import
my_cos = ImportThings(obj="math.cos")

# You can use the imported function as you would expect
cos_of_0 = my_cos.obj(0)
assert cos_of_0 == 1


# A string whose value cannot be imported will raise an error
try:
    ImportThings(obj="foo.bar")
except ValidationError as e:
    print(e)
    """
    1 validation error for ImportThings
    obj
      Invalid python path: No module named 'foo.bar' [type=import_error, input_value='foo.bar', input_type=str]
    """


# Actual python objects can be assigned as well
my_cos = ImportThings(obj=cos)
my_cos_2 = ImportThings(obj="math.cos")
assert my_cos == my_cos_2
