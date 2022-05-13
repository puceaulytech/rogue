import mapgen

generated_map = mapgen.AbstractMap(30, 30, max_rooms=4)
generated_map.generate_random()
generated_map.display()
