import pygame

from pygame.locals import *

import optparse, os
from math import fabs

#DIMENSIONS
SCREEN_SIZE_X = 800
SCREEN_SIZE_Y = 600

NODE_SIZE = 20

#ENTITIES
NONE = 0
PLAYER = 1
TARGET = 2
WALL = 3
PATH = 4
LOWESTFSCORE = 5
INCLOSEDLIST = 6
INOPENLIST = 7

#A* LIST TYPES
OPENLIST = 0
CLOSEDLIST = 1

#MOVEMENT COSTS
HORIZONTAL_MOVE = 10
DIAGONAL_MOVE = 14

#ALGORITHM RECONSTITUTION
RECONSTITUTION_ALGO_DELAY = 10
RECONSTITUTION_PATH_DELAY = 250

class Node():
	'''
	Class that represent each node of the graph.
	'''

	def __init__(self, coordinates, entities = NONE):
		self.coordinates = coordinates
		self.entities = entities

		self.f_score = None
		self.g_score = None
		self.h_score = None

		self.parent_node = None
		self.parent_move_cost = None

		self.list_type = None

	def FScoreDetermination(self, open_list):
		'''
		Determine the F Score regarding the G and H
		scores.
		'''

		self.f_score = self.g_score + self.h_score

		#if this is the new lowest f score of the open list
		if self.f_score < open_list._getNodes()[0]._getFScore():
			open_list.resort(self)

	def _getEntities(self):
		'''
		Return the entities type of this node.
		'''

		return self.entities

	def _getGScore(self):
		return self.g_score
	def _getHScore(self):
		return self.h_score

	def _getFScore(self):
		return self.f_score

	def _getNeighborNodes(self, graph):
		'''
		Return the neighbor nodes of this node.
		Ignoring the WALL node and the node in the
		closed list.
		'''

		neighbors = []

		neighbor_coordinates = {
			'top': (self.coordinates[0], self.coordinates[1] - 1),
			'bottom': (self.coordinates[0], self.coordinates[1] + 1),
			'left': (self.coordinates[0] - 1, self.coordinates[1]),
			'right': (self.coordinates[0] + 1, self.coordinates[1]),
			'topleft': (self.coordinates[0] - 1, self.coordinates[1] - 1),
			'topright': (self.coordinates[0] + 1, self.coordinates[1] - 1),
			'bottomleft': (self.coordinates[0] - 1, self.coordinates[1] + 1),
			'bottomright': (self.coordinates[0] + 1, self.coordinates[1] + 1)
		}

		#check the edges screen before adding neighbors
		if self.coordinates[0] <= 0:
			if 'left' in neighbor_coordinates: neighbor_coordinates.pop('left')
			if 'topleft' in neighbor_coordinates: neighbor_coordinates.pop('topleft')
			if 'bottomleft' in neighbor_coordinates: neighbor_coordinates.pop('bottomleft')

		if self.coordinates[0] >= SCREEN_SIZE_X/NODE_SIZE - 1:
			if 'right' in neighbor_coordinates: neighbor_coordinates.pop('right')
			if 'topright' in neighbor_coordinates: neighbor_coordinates.pop('topright')
			if 'bottomright' in neighbor_coordinates: neighbor_coordinates.pop('bottomright') 

		if self.coordinates[1] <= 0:
			if 'top' in neighbor_coordinates: neighbor_coordinates.pop('top')
			if 'topleft' in neighbor_coordinates: neighbor_coordinates.pop('topleft')
			if 'topright' in neighbor_coordinates: neighbor_coordinates.pop('topright')

		if self.coordinates[1] >= SCREEN_SIZE_Y/NODE_SIZE - 1:
			if 'bottom' in neighbor_coordinates: neighbor_coordinates.pop('bottom')
			if 'bottomleft' in neighbor_coordinates: neighbor_coordinates.pop('bottomleft')
			if 'bottomright' in neighbor_coordinates: neighbor_coordinates.pop('bottomright')


		#do not allow all diagonal moves if the player is next to a WALL node
		if 'top' in neighbor_coordinates:
			if graph[neighbor_coordinates['top']]._getEntities() == WALL:
				if 'topleft' in neighbor_coordinates: neighbor_coordinates.pop('topleft')
				if 'topright' in neighbor_coordinates: neighbor_coordinates.pop('topright')

		if 'bottom' in neighbor_coordinates:
			if graph[neighbor_coordinates['bottom']]._getEntities() == WALL:
				if 'bottomleft' in neighbor_coordinates: neighbor_coordinates.pop('bottomleft')
				if 'bottomright' in neighbor_coordinates: neighbor_coordinates.pop('bottomright')

		if 'right' in neighbor_coordinates:
			if graph[neighbor_coordinates['right']]._getEntities() == WALL:
				if 'topright' in neighbor_coordinates: neighbor_coordinates.pop('topright')
				if 'bottomright' in neighbor_coordinates: neighbor_coordinates.pop('bottomright')

		if 'left' in neighbor_coordinates:
			if graph[neighbor_coordinates['left']]._getEntities() == WALL:
				if 'topleft' in neighbor_coordinates: neighbor_coordinates.pop('topleft')
				if 'bottomleft' in neighbor_coordinates: neighbor_coordinates.pop('bottomleft')

		for c in neighbor_coordinates:
			node = graph[neighbor_coordinates[c]]

			if node._getEntities() is not WALL and \
			node._getList() is not CLOSEDLIST: #ignore nodes in closed list
				neighbors.append(node)

				#set the movement cost between the node and his nodes
				if c in ['top', 'bottom', 'right', 'left']:
					node._setMovementCostFromParent(HORIZONTAL_MOVE)

				elif c in ['topleft', 'topright', 'bottomleft', 'bottomright']:
					node._setMovementCostFromParent(DIAGONAL_MOVE)

		return neighbors

	def _getList(self):
		'''
		Return the list where the node is contained.
		'''
		
		return self.list_type

	def _getMovementCostFromParent(self):
		return self.parent_move_cost

	def _getCoordinates(self):
		'''
		Return the coordinates on the graph of the node.
		'''

		return self.coordinates

	def _getParent(self):
		return self.parent_node

	def _setParent(self, node):
		self.parent_node = node

	def _setMovementCostFromParent(self, cost):
		'''
		Set the movement cost from his parent to this node.
		'''

		self.parent_move_cost = cost

	def _setGScore(self, score):
		self.g_score = score

	def _setHScore(self, score):
		self.h_score = score

	def _setList(self, list_type):
		'''
		Set in what list this node is.
		'''

		self.list_type = list_type

	def _setEntities(self, entities):
		self.entities = entities

class AStarList():
	'''
	Class for handling open list and closed list
	for the A* algorithm.
	'''

	def __init__(self, list_type):
		self.nodes = []

		self.list_type = list_type

	def addNode(self, node):
		'''
		Add a node to the list.
		'''

		self.nodes.append(node)

		node._setList(self.list_type)

	def removeNode(self, node):
		'''
		Remove a node from the list.
		'''

		self.nodes.remove(node)

	def resort(self, node):
		'''
		Replace the lowest f score on top of the list.
		'''

		self.nodes = [node] + self.nodes

	def _getNodes(self):
		'''
		Return the list of nodes contained in the list.
		'''

		return self.nodes

	def _getNodeWithLowestFScore(self):
		'''
		Return the node with the lowest F score.
		'''

		lowest = self.nodes[0]
		
		#for n in self.nodes:
		#	if n._getFScore() < lowest._getFScore():
		#		lowest = n

		return lowest

def reconstruct_path(graph, target_coordinates):
	'''
	Reconstruct the path from the player to the target.
	'''

	path = []

	parent = graph[target_coordinates]._getParent()

	while parent is not None:
		path.append(parent)

		parent = parent.parent_node

	return path

def heuristic_distance(p_coordinate, t_coordinate):
	'''
	Return the estimated distance between player and target
	he wants to reach. It uses the Manhattan method.
	'''

	distance = 0

	x_distance = fabs(p_coordinate[0] - t_coordinate[0])
	y_distance = fabs(p_coordinate[1] - t_coordinate[1])

	distance = (x_distance + y_distance) * HORIZONTAL_MOVE

	return distance

def find_path(graph, player_coordinates, target_coordinates):
	'''
	Find the shortest path between PLAYER entities
	and the TARGET one using A*.
	'''

	start_time = pygame.time.get_ticks()

	#record all the steps of the algorithm in an orderer list to be traced back later
	algorithm_steps = []

	#the open and closed lists
	open_list = AStarList(list_type = OPENLIST)
	closed_list = AStarList(list_type = CLOSEDLIST)

	start_node = graph[player_coordinates] #the start node

	open_list.addNode(start_node) #add the start node to the open list

	#set G, H and F score of the initial node
	start_node._setGScore(0)
	start_node._setHScore(heuristic_distance(player_coordinates, target_coordinates))
	start_node.FScoreDetermination(open_list)

	#main loop of the algorithm
	while len(open_list._getNodes()) > 0:
		current_node = open_list._getNodeWithLowestFScore()

		algorithm_steps.append('choose_lowest_f_score:%s,%s' % current_node._getCoordinates())

		#if the current node is the TARGET node
		if current_node._getEntities() == TARGET:
			final_time = pygame.time.get_ticks() - start_time

			print 'Search time :', final_time, 'ms'

			#return reconstruct_path(graph, target_coordinates)
			return reconstruct_path(graph, target_coordinates), algorithm_steps

		#remove the current node from the open list and add it to the closed list
		open_list.removeNode(current_node)
		closed_list.addNode(current_node)

		algorithm_steps.append('add_to_closed_list:%s,%s' % current_node._getCoordinates())

		for neighbor in current_node._getNeighborNodes(graph):
			tentative_g_score = current_node._getGScore() + neighbor._getMovementCostFromParent() #g score of this one of the neigbors of the current node
		
			if neighbor._getList() is not OPENLIST:
				open_list.addNode(neighbor)

				tentative_is_better = True

				algorithm_steps.append('add_to_open_list:%s,%s' % neighbor._getCoordinates())

			elif tentative_g_score < neighbor._getGScore():
				tentative_is_better = True

			else:
				tentative_is_better = False

			if tentative_is_better:
				neighbor._setParent(current_node)
				neighbor._setGScore(tentative_g_score)
				neighbor._setHScore(heuristic_distance(neighbor._getCoordinates(), target_coordinates))	
				neighbor.FScoreDetermination(open_list)

	return -1

def init_graph(load_from_file, path_file):
	
	'''
	Init the graph.
	'''

	graph = {}

	#create an empty graph
	for x in xrange(0, SCREEN_SIZE_X/NODE_SIZE):
		for y in xrange(0, SCREEN_SIZE_Y/NODE_SIZE):
			graph[x, y] = Node((x, y))	

	if load_from_file:
		#load the graph from the given file
		graph_file = open(path_file, 'r')

		lines = graph_file.readlines()
		
		for line in lines:
			str_coordinates, str_node_type = line.split(' ')

			coordinates = int(str_coordinates.split(',')[0]), int(str_coordinates.split(',')[1])

			node_type = int(str_node_type)

			graph[coordinates] = Node(coordinates, node_type)

		graph_file.close()

	return graph

def save_graph(graph, path_file):
	'''
	Save the graph in a plain text file.
	'''

	graph_file = open(path_file, 'w')

	for c in graph:
		if graph[c]._getEntities() not in [PLAYER, TARGET, PATH, INOPENLIST, INCLOSEDLIST, LOWESTFSCORE]:
			s = str(c[0]) + ',' + str(c[1]) + ' ' + str(graph[c]._getEntities())

			graph_file.write(s + '\n')

	graph_file.close()

def draw_graph(screen):
	'''
	Draw the graph on the screen.
	'''

	#draw vertical lines
	for x in xrange(0, SCREEN_SIZE_X/NODE_SIZE):
		pygame.draw.line(screen, (0, 0, 0), (x * NODE_SIZE, 0), (x * NODE_SIZE, SCREEN_SIZE_Y))

	#draw horizontal lines
	for y in xrange(0, SCREEN_SIZE_Y/NODE_SIZE):
		pygame.draw.line(screen, (0, 0, 0), (0, y * NODE_SIZE), (SCREEN_SIZE_X, y * NODE_SIZE))

def draw_entities(screen, graph):
	'''
	Draw the entities on the screen.
	'''

	for c in graph:
		pos = c[0] * NODE_SIZE, c[1] * NODE_SIZE #c is the coordinates of the entities on the graph 

		if graph[c]._getEntities() == PLAYER:
			pygame.draw.rect(screen, (0, 255, 0), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

		if graph[c]._getEntities() == TARGET:
			pygame.draw.rect(screen, (255, 0, 0), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

		if graph[c]._getEntities() == WALL:
			pygame.draw.rect(screen, (84, 84, 84), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

		if graph[c]._getEntities() == PATH:
			pygame.draw.rect(screen, (0, 0, 255), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

		if graph[c]._getEntities() == LOWESTFSCORE:
			pygame.draw.rect(screen, (111, 0, 255), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

		if graph[c]._getEntities() == INOPENLIST:
			pygame.draw.rect(screen, (202, 255, 112), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

		if graph[c]._getEntities() == INCLOSEDLIST:
			pygame.draw.rect(screen, (255, 127, 36), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

		if graph[c]._getEntities() == PATH:
			pygame.draw.rect(screen, (152, 245, 255), (pos[0], pos[1], NODE_SIZE, NODE_SIZE))

def reconstruct_algorithm(screen, graph, steps, last_step_time = 0, index = 0):
	'''
	Reconstruct the algorithm process.
	'''

	if pygame.time.get_ticks() - last_step_time >= RECONSTITUTION_ALGO_DELAY:
		current_step = steps[index]

		step_type, node_c = current_step.split(':')
		coordinates = int(node_c.split(',')[0]), int(node_c.split(',')[1])

		if graph[coordinates]._getEntities() not in [PLAYER, TARGET]:
			if step_type == 'choose_lowest_f_score':
				graph[coordinates]._setEntities(LOWESTFSCORE)

			elif step_type == 'add_to_open_list':
				graph[coordinates]._setEntities(INOPENLIST)

			elif step_type == 'add_to_closed_list':
				graph[coordinates]._setEntities(INCLOSEDLIST)

		last_step_time = pygame.time.get_ticks()

		index += 1

	return last_step_time, index

def draw_reconstructed_path(screen, graph, path, last_step_time = 0, index = 0):
	'''
	Reconstruct the path from the startpoint to the target.
	'''

	if pygame.time.get_ticks() - last_step_time >= RECONSTITUTION_PATH_DELAY:
		if path[index]._getEntities() not in [PLAYER, TARGET]:
			path[index]._setEntities(PATH)

		last_step_time = pygame.time.get_ticks()

		index -= 1

	return last_step_time, index

def pathfinder(graph_file, load_from_file):
	pygame.init()

	screen = pygame.display.set_mode((SCREEN_SIZE_X, SCREEN_SIZE_Y), HWSURFACE|DOUBLEBUF)

	clock = pygame.time.Clock()

	loop = True

	graph = init_graph(load_from_file, graph_file)

	entities_selection = PLAYER

	left_button_pressed = False

	player_coordinates = None
	target_coordinates = None

	path = None
	algorithm_steps = None
	timer_path = 0
	timer_algo = 0
	index_algo = 0
	index_path = 0

	while loop:
		clock.tick(30)

		for event in pygame.event.get():
			if event.type == QUIT:
				loop = False

			if event.type == KEYDOWN:
				if event.key == K_ESCAPE:
					loop = False

				#set the entities selection (PLAYER, TARGER, WALL)
				elif event.key == K_p:
					entities_selection = PLAYER

				elif event.key == K_t:
					entities_selection = TARGET

				elif event.key == K_w:
					entities_selection = WALL
	
				elif event.key == K_SPACE:
					#check if a player and a target is set and start the path search
					if player_coordinates is not None and target_coordinates is not None:
						result =  find_path(graph, player_coordinates, target_coordinates)

						if result is not -1:
							path, algorithm_steps = result

							index_path = len(path) - 1

				elif event.key == K_s:
					#save the graph for further use
					save_graph(graph, graph_file)				

					load_from_file = True

				elif event.key == K_c:
					#clear the previous path
					path, algorithm_steps = None, None
					timer_path, timer_algo = 0, 0
					index_algo, index_path = 0, 0

					graph = init_graph(load_from_file, graph_file)

			if event.type == MOUSEBUTTONDOWN:
				if event.button == 1:
					left_button_pressed = True

			if event.type == MOUSEBUTTONUP:
				if event.button == 1:
					left_button_pressed = False

			if left_button_pressed:
				pos = pygame.mouse.get_pos()

				coordinates = pos[0]/NODE_SIZE, pos[1]/NODE_SIZE					

				#it can have only one PLAYER entitie on the graph
				#so it checks if the graph already contain a PLAYER
				#if so, it updates the position of this entitie
				if entities_selection == PLAYER:
					#erase the TARGET previously on this node
					if graph[coordinates]._getEntities() == TARGET:
						target_coordinates = None

					if player_coordinates is None:
						graph[coordinates]._setEntities(PLAYER)

						player_coordinates = coordinates

					else:
						graph[player_coordinates]._setEntities(NONE)

						graph[coordinates]._setEntities(PLAYER)

						player_coordinates = coordinates


				#do the exact same checks as the PLAYER entities for
				#TARGET entities
				elif entities_selection == TARGET:
						
					#erase the PLAYER previously on this node
					if graph[coordinates]._getEntities() == PLAYER:
						player_coordinates = None

					if target_coordinates is None:
						graph[coordinates]._setEntities(NONE)
		
						target_coordinates = coordinates
						
					else:
						graph[target_coordinates]._setEntities(NONE)

						graph[coordinates]._setEntities(TARGET)

						target_coordinates = coordinates

				elif entities_selection == WALL:

					#erase the PLAYER or TARGET previously on this node
					if graph[coordinates]._getEntities() == PLAYER:
						player_coordinates = None

					elif graph[coordinates]._getEntities() == TARGET:
						target_coordinates = None

					graph[coordinates]._setEntities(WALL)

		screen.fill((255, 255, 255))

		draw_graph(screen)
		draw_entities(screen, graph)

		if algorithm_steps is not None:
			if index_algo < len(algorithm_steps):
				timer_algo, index_algo = reconstruct_algorithm(screen, graph, algorithm_steps, timer_algo, index_algo)

		if path is not None and index_algo >= len(algorithm_steps) -1:
			if index_path >= 0:
				timer_path, index_path = draw_reconstructed_path(screen, graph, path, timer_path, index_path)

		pygame.display.update()

if __name__ == '__main__':
	parser = optparse.OptionParser('usage: %prog [options] filename')

	parser.add_option('--node_size', dest = 'node_size', default = 20, type = 'int', help = 'side in pixel of the nodes (square)')
	parser.add_option('--algorithm_reconstitution_delay', dest = 'algo_r_delay', default = 50, type = 'int',
		help = 'delay between each step of the algorithm reconstitution in ms')
	parser.add_option('--path_reconstitution_delay', dest = 'path_r_delay', default = 250, type = 'int',
		help = 'delay between each step of the path reconstitution in ms')

	options, args = parser.parse_args()

	if len(args) != 1:
		parser.error('Incorrect number of arguments.')

	NODE_SIZE = options.node_size
	RECONSTITUTION_ALGO_DELAY = options.algo_r_delay
	RECONSTITUTION_PATH_DELAY = options.path_r_delay

	graph_file = args[0]

	load_from_file = False

	if os.path.exists(graph_file):	
		load_from_file = True

	pathfinder(graph_file, load_from_file)
