import mapgen

m = mapgen.Map(30, 30, max_rooms=9)
m.generate_random()
m.display()
