# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 16:47:05 2023

@author: cornelissennaj
"""
import json
from itertools import combinations
from .util import overlay_image, Direction
from .predicates import Predicate, Simple, Merged, Deliverable, Family, PredQuality
   
class RecipeBook(dict):
    
    def __init__(self, recipe_families, base_ingredients=dict(), serve_bases=set()):
        self.recipe_families = dict()
        self.base_ingredients = dict()
        #self.serve_bases = set()

        for r in recipe_families:
            self.recipe_families[r.family_id] = r

        self.recipe_dict = dict()
        self.tool_recipes = dict()
        self.merge_recipes = set()
        self.simple_ingredients = set()
        self.deliverables = set()
        self.flawed = list()
        
        self.expand_recipe_families(self.recipe_families)
        
        super().__init__(recipe_families=self.recipe_families, 
                         base_ingredients=self.base_ingredients,
                         recipe_dict=self.recipe_dict,
                         tool_recipes=self.tool_recipes,
                         merge_recipes=list(self.merge_recipes),
                         simple_ingredients=list(self.simple_ingredients),
                         deliverables=list(self.deliverables)  )      


    def to_json_string(self):
        return json.dumps(self)
        
    def from_json_string(json_str):
        return RecipeBook.from_json_object(json.loads(json_str))
    
    def from_json_object(json_obj):       
        rfs = []
        for r in json_obj['recipes']:
            rfs.append(RecipeFamily.from_json_object(r))
        
        return RecipeBook(rfs)

    def get_recipe(self, unique_name):
        if unique_name in self.recipe_dict:
            return self.recipe_dict[unique_name]
        return None

    def get_recipe_family(self, family_id):
        if family_id in self.recipe_families:
            return self.recipe_families[family_id]
        return None

    def expand_recipe_families(self, rfs):
        for rf_id, rf in rfs.items():            
            for b_i in rf.base_ingredient:
                assert not b_i in self.base_ingredients, "Ingredient can only be base ingredient of one recipe family"
                self.base_ingredients[json.dumps(b_i)] = rf.family_id
                for r in rf.expand_recipes():
                    self.register_recipe(r)
    
    def add_flawed_recipes(self, flaws):
        if not flaws:
            return
        
        flawed = []
        
        # Add flawed versions of this recipe
        for r in self.recipe_dict.values():
                        
            u_flawed = [x for x in r.serve_base if str(x) in flaws] 
            i_flawed = [x for x in r.base_ingredient if str(x) in flaws] 
            j_flawed = [x for x in r.toppings if str(x) in flaws] 
                        
            if not u_flawed and not i_flawed and not j_flawed:
                continue

            # For each combination of flawed serving base
            for u in range(0, len(u_flawed)+1):
                for c_serve in combinations(u_flawed, u):
                    for c in c_serve: c.quality = flaws[str(c)]['fault_type'] # mess up this subset of predicates

                    # For each combination of flawed base ingredients
                    for i in range(0, len(i_flawed)+1):
                        for c_base in combinations(i_flawed, i):
                            for c in c_base: c.quality = flaws[str(c)]['fault_type'] # mess up this subset of predicates

                            # For each possible combination of flawed toppings
                            for j in range(0, len(j_flawed)+1): 
                                for c_top in combinations(j_flawed, j):
                                    for c in c_top: c.quality = flaws[str(c)]['fault_type'] # mess up this subset of predicates
                                    flawed.append(Recipe(serve_base=r.serve_base, base_ingredient=r.base_ingredient, toppings=r.toppings, family_id=r.family_id))

                                    for c in c_top: c.quality = PredQuality.GOOD # clean up this subset of predicates
                            for c in c_base: c.quality = PredQuality.GOOD # clean up this subset of predicates
                    for c in c_serve: c.quality = PredQuality.GOOD # clean up this subset of predicates
    
        self.flawed.extend(flawed)
        for r in flawed:
            self.register_recipe(r)
    
    def register_recipe(self, r):     
        total_length = len(r.serve_base + r.base_ingredient + r.toppings)       
        if total_length == 0:
            return
        
        # Add the basic recipe reference
        self.recipe_dict[r.unique_name] = r
        
        # Add the deliverable recipes
        if total_length > 1:
            self.deliverables.add(r)

        # Register either as a merge recipe
        if total_length > 1:
            self.merge_recipes.add(r)
        else:
            if len(r.serve_base) == 1:
                predType = r.serve_base[0].name
                if predType == Simple.name:
                    # Or register as a simple recipe
                    self.simple_ingredients.add(r)
                else:
                    # Or register as specific tool recipe
                    new_recipe = Recipe(serve_base=r.serve_base[0].args, base_ingredient=r.base_ingredient, toppings=r.toppings)
                    self.register_tool_recipe(new_recipe, r, predType)
                    self.register_recipe(new_recipe)
                    
            if len(r.base_ingredient) == 1:
                predType = r.base_ingredient[0].name
                if predType == Simple.name:
                    # Or register as a simple recipe
                    self.simple_ingredients.add(r)
                else:
                    # Or register as specific tool recipe
                    new_recipe = Recipe(serve_base=r.serve_base, base_ingredient=[], toppings=r.base_ingredient[0].args)
                    self.register_tool_recipe(new_recipe, r, predType)
                    self.register_recipe(new_recipe)  

            if len(r.toppings) == 1:
                predType = r.toppings[0].name
                if predType == Simple.name:
                    # Or register as a simple recipe
                    self.simple_ingredients.add(r)
                else:
                    # Or register as specific tool recipe
                    new_recipe = Recipe(serve_base=r.serve_base, base_ingredient=r.base_ingredient, toppings=r.toppings[0].args)
                    self.register_tool_recipe(new_recipe, r, predType)
                    self.register_recipe(new_recipe)

    def register_tool_recipe(self, in_r, out_r, predType, overwrite=False):
        if not predType in self.tool_recipes:
            self.tool_recipes[predType] = dict()
        self.tool_recipes[predType][json.dumps(in_r)] = out_r
        
    def register_recipes(self, toolMap, overwrite=False):
        # for each tool - predicate association
        for tool, predType in toolMap.items():
            
            if overwrite:
                tool.RECIPES.clear()
            
            if predType == Merged.name:
                for r in self.merge_recipes:
                    # Add the basic recipe references to their recipe SET
                    tool.RECIPES.add(json.dumps(r))

            elif predType == Deliverable.name:
                for d in self.deliverables:
                    # Add the deliverable recipe references to their recipe SET
                    tool.RECIPES.add(json.dumps(d))
            else:
                if predType in self.tool_recipes:
                    # Register specific tool actions to their recipe DICT
                    t_recipes = self.tool_recipes[predType].items()
                    for in_, out_ in t_recipes:
                        tool.RECIPES[in_] = json.dumps(out_)
    
    def preload_agent_images(self, agent_basefiles=[]):        
        for a in agent_basefiles:
            a_south = Direction.South().directional_img(a)
            for r in list(self.recipe_dict.values()) + self.flawed:
                overlay_image(overlay=r.get_img(), base=a_south, box=(0.3, 0.6, 0.7, 1.0))
                
class RecipeFamily(dict):
   
    def __init__(self, family_id, serve_base=['plate'], base_ingredient=[], toppings=[], min_toppings=0, max_toppings=3, base_score=30):
        self.family_id = family_id
        self.serve_base = RecipeFamily.sorted_list(serve_base)
        self.base_ingredient = RecipeFamily.sorted_list(base_ingredient)
        self.toppings = RecipeFamily.sorted_list(toppings)
        self.min_toppings = min_toppings
        self.max_toppings = max_toppings
        self.base_score = base_score
        
        super().__init__(serve_base=self.serve_base, 
                         base_ingredient=self.base_ingredient, 
                         toppings=self.toppings, 
                         min_toppings=self.min_toppings,
                         max_toppings=self.toppings,
                         base_score=self.base_score,
                         family_id=self.family_id)
        
    def to_json_string(self):
        return json.dumps(self)

    def from_json_string(json_str):
        return RecipeFamily.from_json_object(json.loads(json_str))

    def from_json_object(json_obj):
        family_id = str(json_obj['family_id'])
        serve_base, base_ingredient, toppings = [], [], []
        if 'serve_base' in json_obj:
            serve_base = RecipeFamily.pred_list(json_obj['serve_base'])
        if 'base_ingredient' in json_obj:
            base_ingredient = RecipeFamily.pred_list(json_obj['base_ingredient'])
        if 'toppings' in json_obj:
            toppings = RecipeFamily.pred_list(json_obj['toppings'])

        min_toppings, max_toppings, base_score = 0, 3, 30
        if 'min_toppings' in json_obj:
            min_toppings = json_obj['min_toppings']
        if 'max_toppings' in json_obj:
            max_toppings = json_obj['max_toppings']
        if 'base_score' in json_obj:
            base_score = json_obj['base_score']
        
        return RecipeFamily(family_id, serve_base, base_ingredient, toppings, min_toppings, max_toppings, base_score)
        
    def pred_list(lst):
        preds = []
        for l_str in lst:
            preds.append(Predicate.from_string(l_str))
        preds.sort()
        return preds
    
    def sorted_list(lst):
        preds = [p for p in lst]
        preds.sort()
        return preds
    
    def __str__(self):
        str_ = "recipe family: " + self.family_id + ", "
        str_ += "served on: " + ', '.join(str(x) for x in self.serve_base) + ", "
        str_ += "base ingredient: " + ', '.join(str(x) for x in self.base_ingredient) + ", "
        str_ += "possible toppings: " + ', '.join(str(x) for x in self.toppings)

        return str_
    
    def expand_recipes(self):
        # this generalizes the family to include any number of combinations
        
        mergers = []
        
        # For each combination of serving base
        for u in range(0, len(self.serve_base)+1):
            for c_serve in combinations(self.serve_base, u):

                # For each combination of base ingredients
                for i in range(0, len(self.base_ingredient)+1):
                    for c_base in combinations(self.base_ingredient, i):
                        fam_id = "" if len(c_base)==0 else self.family_id

                        # For each possible combination of toppings
                        for j in range(0, self.max_toppings+1):                
                            for c_top in combinations(self.toppings, j):
                                mergers.append(Recipe(serve_base=c_serve, base_ingredient=c_base, toppings=c_top, family_id=fam_id)) 
                    
        return mergers
    
class Recipe(dict):
    def __init__(self, serve_base=['plate'], base_ingredient=[], toppings=[], score=30, family_id="", mark=None):      
        
        self.serve_base = Recipe.sorted_list( serve_base )
        self.base_ingredient = Recipe.sorted_list( base_ingredient )
        self.toppings = Recipe.sorted_list( toppings )
        self.score = score
        self.family_id = family_id
        if not base_ingredient:
            self.family_id = ""
        self.mark = mark
        self.init_dict()


    def init_dict(self):
        self.unique_name = self.get_unique_name()
        self.display_name = self.get_display_name()
        super().__init__(serve_base=self.serve_base, 
                         base_ingredient=self.base_ingredient, 
                         toppings=self.toppings, 
                         family_id=self.family_id, 
                         unique_name=self.unique_name,
                         display_name=self.display_name,
                         resource_name=self.get_img(),
                         mark=self.mark)
        
    def set_mark(self, mark):
        self.mark = mark
        self.init_dict()

    
    def set_family_id(self, f_id):
        self.family_id = f_id
        self.init_dict()
        
    def get_unmarked(self):
        cp = self.copy()
        cp.set_mark(None)
        return cp
    
    def is_quality_good(self):
        for i in self.base_ingredient + self.serve_base + self.toppings:
            if not i.is_quality_good():
                return False
        return True
    
    def get_good_quality(self):
        cp = self.copy()
        for x in cp.serve_base: x.set_quality_good()
        for x in cp.base_ingredient: x.set_quality_good()
        for x in cp.toppings: x.set_quality_good()
        cp.init_dict()
        return cp

    
    def get_unique_name(self):
        unique_name = self.family_id.lower()
        if self.base_ingredient:
            unique_name += '_' +'_'.join([i.get_resource_name() for i in self.base_ingredient])
        if self.toppings:
            unique_name += '_with_' + '_'.join([t.get_resource_name() for t in self.toppings])
        if self.serve_base:
            unique_name += '_on_' + '_'.join([b.get_resource_name() for b in self.serve_base])
        return unique_name
    
    def get_display_name(self):
        display_name = self.family_id.capitalize()
        items = self.serve_base + self.base_ingredient + self.toppings
        if len(items) == 1:
           display_name = items[0].get_display_name()
        elif not self.toppings:
           display_name = 'Simple ' + display_name
        else:
            preds = []
            for t in self.toppings:
                preds.extend(t.get_base_preds())
            if len(preds) == 1:
                display_name = str(preds[0]).capitalize() + ' ' + display_name
            else:     
                display_name = ' '.join([str(p).capitalize() for p in preds]) + ' ' + display_name
        return display_name
    
    
    def __eq__(self, other):
        return (self.serve_base == other.serve_base) and (self.base_ingredient == other.base_ingredient) and (self.toppings == other.toppings)

    def __str__(self):
        return self.unique_name
    
    def __hash__(self):
        return hash(json.dumps(self))
    
    def __add__(self, recipe2):
        serve_base = [x for x in self.serve_base + recipe2.serve_base]
        base_ingredient = [x for x in self.base_ingredient + recipe2.base_ingredient]
        toppings = [x for x in self.toppings + recipe2.toppings]
        return Recipe(serve_base, base_ingredient, toppings, score=self.score, family_id=self.family_id+recipe2.family_id)

    def __sub__(self, recipe2):
        serve_base = [x for x in set(self.serve_base) - set(recipe2.serve_base)]
        base_ingredient = [x for x in set(self.base_ingredient) - set(recipe2.base_ingredient)]
        toppings = [x for x in set(self.toppings) - set(recipe2.toppings)]
        return Recipe(serve_base, base_ingredient, toppings, score=self.score, family_id=self.family_id)
    
    def to_json_string(self):
        return json.dumps(self)
    
    def from_str_gen(json_str):
        return Recipe.from_json_gen(json.loads(json_str))
    
    def from_json_gen(json_obj):
        
        fam_id, serve_base, base_ingredient, toppings, mark = "", [], [], [], None
    
        if 'family_id' in json_obj:
            fam_id = json_obj['family_id']
        if 'serve_base' in json_obj:
            serve_base = Recipe.pred_list(json_obj['serve_base'])
        if 'base_ingredient' in json_obj:
            base_ingredient = Recipe.pred_list(json_obj['base_ingredient'])
        if 'toppings' in json_obj:
            toppings = Recipe.pred_list(json_obj['toppings'])
        if 'mark' in json_obj:
            mark = json_obj['mark']
            
        return Recipe(serve_base, base_ingredient, toppings, family_id=fam_id, mark=mark)
    
    def pred_list(lst):
        preds = []
        for l_str in lst:
            preds.append(Predicate.from_string(l_str))
        preds.sort()
        return preds

    def sorted_list(lst):
        preds = [p.deepcopy() for p in lst]
        preds.sort()
        return preds
    
    def get_img(self):
        img = None
        
        for pred in self.serve_base:
            img = overlay_image("ingredients\\"+pred.get_resource_name()+".png", base=img)
                
        folder = "" if self.family_id == "" else self.family_id+"\\"
            
        for pred in self.base_ingredient + self.toppings:
            img = overlay_image("ingredients\\"+folder+pred.get_resource_name()+".png", base=img)
        return img        
    
    def copy(self):
        return Recipe(self.serve_base, self.base_ingredient, self.toppings, score=self.score, family_id=self.family_id, mark=self.mark)

    def get_subtasks(self):
        subtasks = []
        
        total_len = len(self.serve_base) + len(self.base_ingredient) + len(self.toppings)
        
        for pred in self.serve_base:
            if total_len > 1:
                pred_t = Recipe([pred], [], [], family_id = self.family_id)
                resi_t = self - pred_t
                subtasks.append((pred_t, resi_t))    
            elif not isinstance(pred, Simple):
                pred_t = Recipe(serve_base=pred.args, base_ingredient=[], toppings=[])
                subtasks.append((pred_t, pred.name))
           
        for pred in self.base_ingredient:
            if total_len > 1:
                pred_t = Recipe([], [pred], [], family_id = self.family_id)
                resi_t = self - pred_t
                subtasks.append((pred_t, resi_t))
            elif not isinstance(pred, Simple):
                pred_t = Recipe(serve_base=[], base_ingredient=[], toppings=pred.args)
                subtasks.append((pred_t, pred.name))

            
        for pred in self.toppings:
            if total_len > 1:
                pred_t = Recipe([], [], [pred], family_id = self.family_id)
                resi_t = self - pred_t
                subtasks.append((pred_t, resi_t))        
            elif not isinstance(pred, Simple):
                pred_t = Recipe(serve_base=[], base_ingredient=[], toppings=pred.args)
                subtasks.append((pred_t, pred.name)) 
                
        return subtasks