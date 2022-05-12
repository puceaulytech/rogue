import mapgen

generated_map = mapgen.AbstractMap(30, 30, 3)
generated_map.random_map()
generated_map.make_paths()
generated_map.display()
