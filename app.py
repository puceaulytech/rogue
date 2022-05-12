import mapgen

generated_map = mapgen.AbstractMap(30, 30, max_rooms=3)
generated_map.random_map()
generated_map.make_paths()
generated_map.display()

print(generated_map)
