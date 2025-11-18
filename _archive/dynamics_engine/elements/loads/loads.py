"""
"""
# from dynamics_engine.elements.loads.load import Load, GeneralizedLoadVector

# __all__ = ['Loads']

# class Loads:
#     def __init__(self):
#         self._elements: list[Load] = []
    
#     def register_load(self, element: Load):
#         try:
#             used_names = [e.name for e in self._elements]
#             assert element.full_name not in used_names
#         except AssertionError:
#             raise ValueError(
#                 f'\n\n\tNaming conflict for {element.full_name = }.'  
#                 f'\n\t\tUse unique names for dynamic elements.'
#             )
#         self._elements.append(element)
#         return self
