NAME = fly_in
CXX = g++
CXXFLAGS = -std=c++20 -Wall -Wextra -pedantic -O3

HEADERS = flying.hpp graph.hpp parsing.hpp bfs_cost.hpp		\
	greedy_planner.hpp simulator.hpp map_check.hpp plan_ner.hpp

all: $(NAME)

$(NAME): main.cpp $(HEADERS) Makefile
	$(CXX) $(CXXFLAGS) main.cpp -o $(NAME)

run: $(NAME)
	./$(NAME) ../maps/medium/01_dead_end_trap.txt

debug: CXXFLAGS += -g -O0
debug: fclean $(NAME)
	gdb ./$(NAME)

sanitize: CXXFLAGS += -fsanitize=address -fno-omit-frame-pointer -g
sanitize: fclean $(NAME)
	./$(NAME) ../maps/medium/01_dead_end_trap.txt

clean:
	@rm -f *.o

fclean:
	@rm -f $(NAME)

re: fclean all

.PHONY: all run debug sanitize clean fclean re
