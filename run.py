import pickle
import re
import numpy as np
import scipy as sp
import lda
from nltk.corpus import stopwords as stop
from nltk.tokenize import word_tokenize as token
from nltk.tokenize import sent_tokenize as sents
from nltk.stem import SnowballStemmer as stemmer
from nltk.stem import WordNetLemmatizer as lemma
from nltk import pos_tag as pos
from nltk import RegexpParser as regex_parse
from os import listdir
from pprint import pprint
from math import *
from sklearn.cluster import Ward
import matplotlib.pyplot as plt
from pulp import *

STOP_WORDS = set(stop.words('english'))
GOOD_POS = {'JJ','JJR','JJS','NN','NNS','NNP','NNPS'}#,'VB','VBD','VBG','VBN','VBP','VBZ'}
SNOW = stemmer('english')
LEMMATE = lemma()
CHUNK = regex_parse('CONCEPT: {<JJ>*<NN>(<CC|IN>?<NN>)?}') #concept tagging
FORCE_TAGS = {'prof':'NP'}
NPTEL_STOP_WORDS = {'time','slide','refer','x','one','equal','minus','u','also','plus','see','like','mean','get','let','value','say','point','two','ha','n','y',
					'case','d','going','go','c','know','1','2','3','take','r','p','look','would','wa','v','term','k','first','f','thing','may','e','particular',
					'example','different','find','problem','actually','use','therefore','given','m','give','way','come','z','called','need','want','4','write',
					'change','l','h','another','using','right','second','used','kind','much','important','g','le','side','doe','well','constant','method','part',
					'j','something','alpha','beta','gamma','delta','could','q','next','variable','course','lecture','three','put','done','output','high','small',
					'theta','many','input','even','okay','really','since','divided','basically','nothing','got','start','back','becomes','seen','product','consider',
					'must','suppose','certain','increase','decrease','parameter','total','w','already','possibly','known','said','place','result','good','try',
					'difference','fact','show','always','happens','similarly','whether','coming','people','upon','remember','various','effect','whatever','naught',
					'star','bar','based','respect','half','earlier','able','last','essentially','greater','getting','low','corresponding','amount','along','available',
					'talk','talking','either','think','percent','situation','shown','discussed','become','keep','written','every','basic','required','new','looking',
					'taking','four','happen','due','left','within','simply','still','define','tell','idea','made','assume','similar','device','specific','lot','co',
					'measure','fixed','definition','around','obviously','trying','today','apply','study','year','dash','draw','column','exactly','test','group',
					'reason','sense','add','indian','turn','later','multiplied','long','entire','depending','approach','instead','better','whereas','clear',
					'etcetera','law','common','together','found','non','obtained','saying','mentioned','whenever','however','department','finally','row','aspect',
					'across','basis','detail','squared','requirement','shall','applied','without','following','true','actual','quite','obtain','considered',
					'increasing','decreasing','day','formula','depends','equivalent','easily','several','might','least','require','complete','open','close',
					'institute','name','reduce','mechanism','rather','making','almost','please','note','compared','concerned','choose','answer','view','normally',
					'sorry','generally','typically,','prof','main','final','sometimes','saw','student','assumption','read','determine','directly','easy','difficult',
					'hence','starting','though','otherwise','eta','psi','theta','discussion','interested','usually','dx','towards','measurement','talked',
					'happening','theorem','principle','considering','changing','writing','represent','started','told','run','interesting','giving','statement',
					'developed','procedure','continue','everything','discussing','multiple','outside','inside','remain','anything','somewhere','involved','create',
					'divide','multiple','add','subtract','sub','approximately','approximation','slightly','completely','identify','implies','acting','hour','india',
					'beyond','hour','minute','often','enough','else','concept'}
					
AI_GROUND_TRUTH = [{1},{2},{3},{4,3},{5,3},{6,5,4,3},{7,3},{8,7,3},{9,3},{10,9,3},{11},{12,11},{13,12,11},{14,13,12,11},{15,14,13,12,11},{16},{17,16},{18},{19,18},
				{20,19,18},{21,3,2},{22,21,3,2},{23,22,21,3,2},{24,23,22,21,3,2},{25,16},{26},{27,26},{28,26},{29,28,26},{30,29,28},{31,30,29,28},{32},{33,32},{34,32},
				{35,34,32},{36,32},{37,36,32},{38,29,28},{39},{40,39,20}]

def find_stop_words(directory, tfidf_cutoff=0.0005): #finds stopwords from a corpus of documents
	transcripts = listdir(directory)
	print 'Finding stop words from', len(transcripts), 'documents:'
	doc_freq = {}
	all_vocab = []
	num_terms = []
	for doc in transcripts:
		print doc
		fd = open(directory+'/'+doc)
		text = fd.read().lower()		
		fd.close()
		text = re.sub('[^\w\s]',' ',text) #remove non-words
		words = token(text)
		words = [LEMMATE.lemmatize(i) for i in words] #lemmatisation
		words = [SNOW.stem(i) for i in words] #stemming
		num_terms.append(len(words))
		vocab = {}
		for i in words:
			if i in vocab:
				vocab[i] += 1
			else:
				vocab[i] = 1
		for i in vocab.keys():
			if i in doc_freq:
				doc_freq[i] += 1
			else:
				doc_freq[i] = 1
		all_vocab.append(vocab)
	stop_words = []
	for term in doc_freq.keys():
		idf = log(len(transcripts)/doc_freq[term])
		tf_idf = [(float(all_vocab[i][term])/num_terms[i])*idf if term in all_vocab[i] else 0 for i in range(len(transcripts))]
		print (tf_idf)
		cutoff = [tf_idf[i] > tfidf_cutoff for i in range(len(tf_idf))]
		if (any(cutoff)):
			stop_words.append(term)
	print(stop_words)
	
def compare_hierarchies(hier_1, hier_2=AI_GROUND_TRUTH, not_include_self=True): #evaluates a ground truth and an evaluated hierarchy
	print '=Comparing Hierarchies for Model Evaluation='
	if(len(hier_1)!=len(hier_2)):
		print 'Error: Hierarchies must be of same length.'
		return None
	tp = 0
	tn = 0
	fp = 0
	fn = 0
	for i in range(len(hier_1)):
		print i, hier_1[i], hier_2[i]
		tp += len(hier_2[i])-int(not_include_self)
		tn += len(hier_2)-len(hier_2[i])-int(not_include_self)
		fp += len(hier_1[i]-hier_2[i])
		fn += len(hier_2[i]-hier_1[i]);
	precision = float(tp)/(tp+fp)	#how many selected items are relevant?
	recall = float(tp)/(tp+fn)		#how many relevant items are selected?
	f1_score = float(2*tp)/(2*tp+fp+fn)
	corr_coeff = float(tp*tn-fp*fn)/(sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)))
	accuracy = float(tp+tn)/(tp+tn+fp+fn)
	print 'Precision:', precision
	print 'Recall:', recall
	print 'F1 Score:', f1_score
	print 'Correlation Coefficient:', corr_coeff
	print 'Accuracy:', accuracy
	print 'Number of lectures:', tp+fp
	return (precision, recall, f1_score, corr_coeff, accuracy, tp+fp)
		
def get_text_rank(string, k=8, n_occurr=2, d=0.85, thresh=0.001): #returns top k (keyword, score) pairs based on TextRank
	string = string.lower()
	string = re.sub('[^\w\s]',' ',string) #remove non-words
	words = token(string) #tokenise string
	words = [i for i in words if pos([i])[0][1] in GOOD_POS] #part of speech filtering
	words = [i for i in words if (i not in STOP_WORDS and i not in NPTEL_STOP_WORDS)] #remove stop words (english and nptel)
	words = [LEMMATE.lemmatize(i) for i in words] #lemmatisation
	words = [SNOW.stem(i) for i in words] #stemming
	unique = {}
	reverse = {}
	num_words = 0
	for i in words:
		if i not in unique:
			unique[i] = num_words
			reverse[num_words] = i
			num_words += 1
	print 'Running text rank on', num_words, 'unique words...'
	graph = [[0 for i in range(num_words)] for i in range(num_words)]
	#Form co-occurrence matrix
	for i in range(len(words)):
		for j in range(max(0,i-n_occurr),min(i+n_occurr,len(words))):
			graph[unique[words[i]]][unique[words[j]]] = 1
	#Iterate and perform text rank
	err = float('inf')
	score = [1 for i in range(num_words)]
	links = [sum(x) for x in graph]
	while err>thresh:
		new_score = [(1-d)+d*sum([score[j]/links[j] for j in range(num_words) if graph[i][j]==1]) for i in range(num_words)] #Page rank inspired formula
		err = sum([abs(new_score[i]-score[i]) for i in range(num_words)])/num_words
		score = new_score[:]
	keywords = [(reverse[i],score[i]) for i in range(num_words)]
	keywords = sorted(keywords,key=lambda x:x[1],reverse=True)
	if (k>0):
		keywords = keywords[:k]
	return keywords

def bag_of_words(string, pos_tagging = False, stopwords = False, len_gt = False, lemmatisation = False, stemming = False): #outputs a BoW vector for given string
	string = string.lower()
	string = re.sub('[^\w\s]',' ',string) #remove non-words
	words = token(string) #tokenise string
	if pos_tagging: #consider only nouns, adjectives
		words = [i for i in words if pos([i])[0][1] in GOOD_POS]
	if stopwords:
		words = [i for i in words if (i not in STOP_WORDS and i not in NPTEL_STOP_WORDS)]
	if len_gt:
		words = [i for i in words if len(i)>2]
	if lemmatisation:
		words = [LEMMATE.lemmatize(i) for i in words]
	if stemming:
		words = [SNOW.stem(i) for i in words]
	bag = {}
	for i in words:
		if i in bag:
			bag[i] += 1
		else:
			bag[i] = 1
	return bag, len(words)

def dump_bow_scores(directory): #employs and dumps BoW vectors of a given directory of documents
	transcripts = listdir(directory)
	lec_nos = [int(re.sub('[^\d]','',i)) for i in transcripts]
	transcripts = [x for (y, x) in sorted(zip(lec_nos, transcripts))]
	bags = []
	keys = []
	num_w = []
	print 'Employing bag of words on', len(transcripts), 'documents:'
	for doc in transcripts:
		print (doc)
		fd = open(directory+'/'+doc)
		string = fd.read()
		fd.close()
		bag, num = bag_of_words(string,True,True,True,True,True) #bag_of_words(string, pos_tagging, stopwords, len_gt, lemmatisation, stemming)
		bags.append(bag)
		keys.append(set(bag.keys()))
		num_w.append(num)
	pickle.dump((transcripts,bags,keys,num_w),open('data/'+directory+'_bags_all.pickle','w'))		
	
def simple_bow_ordering(bags_file, thresh=9, k=3): #uses BoW dump to output hierarchies and evaluate results with ground truth
	transcripts, bags, keys, num_w = pickle.load(open(bags_file))
	scores = [[0 for i in range(len(transcripts))] for i in range(len(transcripts))]
	print '*SIMPLE BAG OF WORDS ORDERING*', thresh
	#print 'Scoring for', len(transcripts), 'document:'
	for i in range(len(bags)-1):
		#print transcripts[i]
		for j in range(i+1,len(bags)):
			occurs = [bags[i][key]*bags[j][key] for key in keys[i]|keys[j] if (key in keys[i]&keys[j])]
			occurs = sum(occurs)/(num_w[i]+num_w[j])
			scores[i][j] = occurs
			scores[j][i] = occurs
	'''print 'Displaying top-k scores for every document:'
	for i in range(len(transcripts)):
		list_top_k = sorted(zip(scores[i],transcripts), reverse=True)[0:k]
		print transcripts[i], '\t', list_top_k'''
	#print 'Displaying discovered hierarchy:'
	hier_sets = []
	for i in range(len(transcripts)):
		s = [i+1]
		#print transcripts[i]
		for j in range(0,i):
			if (scores[i][j]>=thresh):
				#print '>>', transcripts[j]
				s.append(j+1)
		hier_sets.append(set(s))
	return compare_hierarchies(hier_sets)
	
def dump_textrank_scores(directory): #employs and dumps TextRanked BoW vectors of a given directory of documents
	transcripts = listdir(directory)
	lec_nos = [int(re.sub('[^\d]','',i)) for i in transcripts]
	transcripts = [x for (y, x) in sorted(zip(lec_nos, transcripts))]
	scores = []
	keys = []
	num_w = []
	print 'Employing text rank on', len(transcripts), 'documents:'
	for doc in transcripts:
		print (doc)
		fd = open(directory+'/'+doc)
		string = fd.read()
		fd.close()
		tr = dict(get_text_rank(string,-1))
		scores.append(tr)
		keys.append(set(tr.keys()))
		num_w.append(len(tr))
	pickle.dump((transcripts,scores,keys,num_w),open('data/'+directory+'_textrank_scores.pickle','w'))
	
def textrank_scored_ordering(scores_file, thresh=0.5, k=3): #uses TextRank dump to output hierarchies and evaluate results with ground truth
	transcripts, tr_scores, keys, num_w = pickle.load(open(scores_file))
	scores = [[0 for i in range(len(transcripts))] for i in range(len(transcripts))]
	print '*TEXT RACK SCORED ORDERING*', thresh
	#print 'Scoring for', len(transcripts), 'document:'
	for i in range(len(tr_scores)-1):
		#print transcripts[i]
		for j in range(i+1,len(tr_scores)):
			occurs = [tr_scores[i][key]*tr_scores[j][key] for key in keys[i]|keys[j] if (key in keys[i]&keys[j])]
			occurs = sum(occurs)/(num_w[i]+num_w[j])
			scores[i][j] = occurs
			scores[j][i] = occurs
	'''print 'Displaying top-k scores for every document:'
	for i in range(len(transcripts)):
		list_top_k = sorted(zip(scores[i],transcripts), reverse=True)[0:k]
		print transcripts[i], '\t', list_top_k'''
	#print 'Displaying discovered hierarchy:'
	hier_sets = []
	for i in range(len(transcripts)):
		s = [i+1]
		#print transcripts[i]
		for j in range(0,i):
			if (scores[i][j]>=thresh):
				#print '>>', transcripts[j]
				s.append(j+1)
		hier_sets.append(set(s))
	return compare_hierarchies(hier_sets)

def doc_term_mat_from_bags(bags_file):
	print 'Forming document-term matrix...'
	transcripts, bags, keys, num_w = pickle.load(open(bags_file))
	words = list(set.union(*keys))
	map = dict(zip(words, [i for i in range(len(words))]))
	matrix = np.zeros([len(transcripts), len(words)], int)
	for i in range(len(bags)):
		for j, k in bags[i].iteritems():
			matrix[i][map[j]] = k
	return matrix, words, transcripts
	
def model_lda(bags_file, num_topics_multiplier=0.4, num_iters=1500): #employs LDA on a BoW (TextRanked or Simple) file dump
	print 'Starting Latent Dirichlet Allocation (LDA) Analysis...'
	data, words, transcripts = doc_term_mat_from_bags(bags_file)
	model = lda.LDA(n_topics=int(num_topics_multiplier*len(transcripts)), n_iter=num_iters, random_state=1)
	model.fit(data);
	return (model, words, transcripts)
	
def lda_derived_ordering(bags_file, num_topics_multiplier=0.4, num_iters=1500): #uses LDA analysis to output hierarchies and evaluate results with ground truth
	print '*LDA DERIVED ORDERING*', num_topics_multiplier
	topic_model = model_lda(bags_file, num_topics_multiplier, num_iters)
	doc_topic = topic_model[0].doc_topic_
	transcripts = topic_model[2]
	top_topic = [doc_topic[i].argmax() for i in range(len(transcripts))]
	hier_sets = []
	for i in range(len(transcripts)):
		s = [i+1]
		#print transcripts[i]
		for j in range(0,i):
			if (top_topic[i]==top_topic[j]):
				#print '>>', transcripts[j]
				s.append(j+1)
		hier_sets.append(set(s))
	return compare_hierarchies(hier_sets)
	
def display_lda(model, k=8):
	topic_word = model[0].topic_word_
	print 'Displaying topic-word information:'
	for i, topic_dist in enumerate(topic_word):
		topic_words = np.array(model[1])[np.argsort(topic_dist)][:-k:-1]
		print 'Topic {}: {}'.format(i, ' '.join(topic_words))
	doc_topic = model[0].doc_topic_
	print 'Displaying document-topic information:'
	for i in range(len(model[2])):
		print '{} (top topic: {})'.format(model[2][i], doc_topic[i].argmax())
		
def hac_derived_ordering(bags_file, num_clusters_multiplier=0.4): #uses HAC analysis to output hierarchies and evaluate results with ground truth
	print '*HAC DERIVED ORDERING*', num_clusters_multiplier
	print 'Starting Hierarchical Agglomerative Clustering analysis...'
	data, words, transcripts = doc_term_mat_from_bags(bags_file)
	model =Ward(n_clusters=int(num_clusters_multiplier*len(transcripts))).fit(data)
	clust = model.fit_predict(data)
	hier_sets = []
	for i in range(len(transcripts)):
		s = [i+1]
		#print transcripts[i]
		for j in range(0,i):
			if (clust[i]==clust[j]):
				#print '>>', transcripts[j]
				s.append(j+1)
		hier_sets.append(set(s))
	return compare_hierarchies(hier_sets)	
	
def segment_transcript(all_string, stringency=0.5, len_wt = 0.8, len_mu=8, len_sigma=2): #dynamic programming method to segment transcripts
	all_string = re.sub('\n+','',all_string)
	sections = re.split('[\s]*\([\s]*refer.*?\)[\s]*',all_string,flags=re.IGNORECASE)
	segmented = ''
	for string in sections:
		try:
			sentences = sents(string)
			if (len(sentences)<3): #too short sentences are clubbed with the following paragraph
				raise Exception
			string = string.lower()
			string = re.sub('[^\w\s]',' ',string) #remove non-words
			words = token(string) #tokenise string
			words = [i for i in words if (i not in STOP_WORDS and i not in NPTEL_STOP_WORDS)] #remove stop words
			words = list(set([i for i in words if len(i)>2])) #remove trailing words
			wrd_matrix = [[0 for i in range(len(words))] for j in range(len(sentences))]
			for i in range(len(sentences)):
				for j in range(len(words)):
					if words[j] in sentences[i]:
						wrd_matrix[i][j] = 1
			sim_matrix = [[0 for i in range(len(sentences))] for j in range(len(sentences))]
			for wrd in wrd_matrix:
				occurs_in = [i for i in range(len(sentences)) if wrd[i]==1]
				for i in occurs_in:
					for j in occurs_in:
						sim_matrix[i][j] = 1
						sim_matrix[j][i] = 1
			#init
			density_matrix = [[0.0]]+[[0.0]+[sum([sum(sim_matrix[k][j:i+1]) for k in range(j,i+1)])/(i-j+1)**stringency for j in range(i+1)] for i in range(len(sentences))]
			cost_matrix = [float('inf') for i in range(len(sentences)+1)]
			cost_matrix[0] = 0
			asgn_matrix = [0 for i in range(len(sentences)+1)]
			#minimisation
			for i in range(1,len(sentences)+1):
				for j in range(i):
					new_cost = cost_matrix[j]-(1-len_wt)*density_matrix[i][j]+len_wt*((i-j-len_mu)**2/(2*len_sigma**2))
					if (new_cost<cost_matrix[i]):
						cost_matrix[i] = new_cost
						asgn_matrix[i] = j
			#backtracking
			brkpts = [len(sentences)]
			while (asgn_matrix[brkpts[0]]>0):
				brkpts = [asgn_matrix[brkpts[0]]] + brkpts
			brkpts = [i-1 for i in brkpts]
			prev = 0
			for i in brkpts:
				for j in range(prev,i):
					segmented += sentences[j]+' '
				segmented += sentences[i]+'\n\n'
				prev = i+1
		except:
			segmented += string
	return segmented
	
def grid_search (list_methods = []): #performs grid-search over parameters of the baseline models
	best_params = []
	all_results = []
	all_params = [[6,7,8,9,10,11,12],[0.2,0.3,0.4,0.5,0.6,0.7,0.8],[0.2,0.3,0.4,0.5,0.6,0.7,0.8],[0.2,0.3,0.4,0.5,0.6,0.7,0.8],[0.2,0.3,0.4,0.5,0.6,0.7,0.8],[0.2,0.3,0.4,0.5,0.6,0.7,0.8]]
	method = ['SimpleBOW','TextRank','LDA','LDA+TextRank','HAC','HAC+TextRank']
	for i in list_methods:
		if i==0:
			print '=Grid search for Simple Bag of Words Ordering='
			params = all_params[i]
			max = 0
			param = params[0]
			results = []
			for j in params:
				result = simple_bow_ordering('data/transcripts_bags_all.pickle', j)
				if (result[2]>max):
					param = j
					max = result[2]
				results.append(result)
			best_params.append(param)
			all_results.append(np.transpose(np.asarray(results)))
		elif i==1:
			print '=Grid search for Text Rank Scored Ordering='
			params = all_params[i]
			max = 0
			param = params[0]
			results = []
			for j in params:
				result = textrank_scored_ordering('data/transcripts_textrank_scores.pickle', j)
				if (result[2]>max):
					param = j
					max = result[2]
				results.append(result)
			best_params.append(param)
			all_results.append(np.transpose(np.asarray(results)))
		elif i==2:
			print '=Grid search for Latent Dirichlet Allocation derived Ordering='
			params = all_params[i]
			max = 0
			param = params[0]
			results = []
			for j in params:
				result = lda_derived_ordering('data/transcripts_bags_all.pickle', j)
				if (result[2]>max):
					param = j
					max = result[2]
				results.append(result)
			best_params.append(param)
			all_results.append(np.transpose(np.asarray(results)))
		elif i==3:
			print '=Grid search for LDA+TextRank derived Ordering='
			params = all_params[i]
			max = 0
			param = params[0]
			results = []
			for j in params:
				result = lda_derived_ordering('data/transcripts_textrank_scores.pickle', j)
				if (result[2]>max):
					param = j
					max = result[2]
				results.append(result)
			best_params.append(param)
			all_results.append(np.transpose(np.asarray(results)))
		elif i==4:
			print '=Grid search for Hierarchical Agglomerative Clustering derived Ordering='
			params = all_params[i]
			max = 0
			param = params[0]
			results = []
			for j in params:
				result = hac_derived_ordering('data/transcripts_bags_all.pickle', j)
				if (result[2]>max):
					param = j
					max = result[2]
				results.append(result)
			best_params.append(param)
			all_results.append(np.transpose(np.asarray(results)))
		elif i==5:
			print '=Grid search for HAC+TextRank derived Ordering='
			params = all_params[i]
			max = 0
			param = params[0]
			results = []
			for j in params:
				result = hac_derived_ordering('data/transcripts_textrank_scores.pickle', j)
				if (result[2]>max):
					param = j
					max = result[2]
				results.append(result)
			best_params.append(param)
			all_results.append(np.transpose(np.asarray(results)))
		else:
			print 'Invalid method number:', i
			best_params.append(-1)
			all_results.append(np.zeros(0,float))
	labels = ['precision', 'recall', 'f1_score', 'corr_coeff', 'accuracy']
	for i in range(len(list_methods)):
		for j in range(5):
			plt.plot(all_params[list_methods[i]], all_results[i][j], label=labels[j])
		plt.legend(title='performance measures')
		plt.xlabel('parameters')
		plt.ylabel('measure')
		plt.title('Performance of Method '+method[list_methods[i]]+', across parameters')
		plt.savefig(method[list_methods[i]]+'.png')
		plt.clf()
	return (best_params, all_results)
	
'''def co_occurrence(string, window_size=2, word_occurns={}):
	string = string.lower()
	string = re.sub('[^\w\s]',' ',string) #remove non-words
	words = token(string) #tokenise string
	words = [i for i in words if (i not in STOP_WORDS and i not in NPTEL_STOP_WORDS)] #remove stop words (english and nptel)
	words = [i for i in words if len(i)>2] #remove short words
	words = [LEMMATE.lemmatize(i) for i in words] #lemmatisation
	words = [SNOW.stem(i) for i in words] #stemming
	check_done = set()
	for i in range(len(words)):
		for j in range(max(0,i-window_size),min(i+window_size,len(words))):
			if words[i]==words[j]:
				continue
			if words[i] in word_occurns:
				if words[j] in word_occurns[words[i]]:
					if (words[i],words[j]) in check_done:
						word_occurns[words[i]][words[j]][-1] += 1
					else:
						word_occurns[words[i]][words[j]] += [1]
						check_done.add((words[i],words[j]))
				else:
					word_occurns[words[i]][words[j]] = [1]
			else:
				word_occurns[words[i]] = {words[j] : [1]}
			check_done.add((words[i],words[j]))
	return word_occurns

def dump_concept_relationships(directory, window_size=5, num_cooccur=16, sections_thresh=2):
	transcripts = listdir(directory)
	lec_nos = [int(re.sub('[^\d]','',i)) for i in transcripts]
	transcripts = [x for (y, x) in sorted(zip(lec_nos, transcripts))]
	print 'Employing co-occurrence analysis on words with window size:', window_size, 'number of cooccurrns:', num_cooccur,'section threshold:', sections_thresh, 'of', len(transcripts), 'documents:'
	words = {} #dictionary of word:word:[occurns]
	for doc in transcripts:
		print (doc)
		fd = open(directory+'/'+doc)
		string = fd.read()
		fd.close()
		words = co_occurrence(string, window_size, words)
	for key, val in words.iteritems():
		for word in val.keys():
			if len(val[word])<sections_thresh:
				val.pop(word)
			else:
				if not any([i>=num_cooccur for i in val[word]]):
					val.pop(word)
	for word in words.keys():
		if len(words[word]) == 0:
			words.pop(word)
	pickle.dump(words,open('data/'+directory+'_cooccur_words.pickle','w'))
	return words
	
def display_related_concepts(dumpname):
	data = pickle.load(open(dumpname))
	for key, val in data.iteritems():
		print key
		for i in val:
			print '\t',i'''

def co_occurrence_analysis(string, concept_words, concept_lengths, concept_indices, word_relations = {}, window_size=100): #find related words, not being used in the final implementation?
	print 'Co-occurrence analysis to find related concepts...'
	string = string.lower()
	string = re.sub('[^\w\s]',' ',string) #remove non-words
	words = token(string) #tokenise string
	new_words = []
	i = 0
	while i<len(words):
		found = False
		for j in range(len(concept_words)):
			if i in concept_indices[j]:
				new_words += [concept_words[j]]
				i += concept_lengths[j]
				found = True
				break
		if not found:
			new_words += [words[i]]
			i += 1
	words = [i for i in words if (i not in STOP_WORDS and i not in NPTEL_STOP_WORDS)] #remove stop words (english and nptel)
	words = [i for i in words if len(i)>2] #remove short words
	#words = [LEMMATE.lemmatize(i) for i in words] #lemmatisation
	#words = [SNOW.stem(i) for i in words] #stemming
	check_done = set()
	for i in range(len(words)):
		for j in range(max(0,i-window_size),min(i+window_size,len(words))):
			if words[i]==words[j] or words[i] not in concept_words or words[j] not in concept_words:
				continue
			if words[i] in word_relations:
				if words[j] in word_relations[words[i]]:
					if (words[i],words[j]) in check_done:
						word_relations[words[i]][words[j]][-1] += 1
					else:
						word_relations[words[i]][words[j]] += [1]
						check_done.add((words[i],words[j]))
				else:
					word_relations[words[i]][words[j]] = [1]
			else:
				word_relations[words[i]] = {words[j] : [1]}
			check_done.add((words[i],words[j]))
	return word_relations
	
def check_occurs(check_for, words, thresh=5): #heuristic function for candidate concept phrase extraction
	if all([i in STOP_WORDS|NPTEL_STOP_WORDS or len(i)<3 for i in check_for]):
		return (False, [])
	found = [i for i in range(len(words)-len(check_for)+1) if words[i:i+len(check_for)] == check_for]
	if len(found) >= thresh:
		return (True, found)
	else:
		return (False, found)
		
def candidate_concept_phrases(string, thresh=5): #given a string, does POS pattern matching and uses threshold occurrence heuristics to output a candidate set of concept phrases
	print 'Finding candidate concept phrases...'
	string = string.lower()
	string = re.sub('[^\w\s]',' ',string) #remove non-words
	words = token(string) #tokenise string
	tree = CHUNK.parse(pos(words))
	list_concepts = []
	set_concepts = []
	for a in tree:
		if str(type(a)) == "<class 'nltk.tree.Tree'>":
			if a.label() == 'CONCEPT':
				concept = []
				for i in range(len(a)):
					concept += [a[i][0]]
				c = check_occurs(concept, words, thresh)
				if c[0] and (concept not in set_concepts):
					list_concepts.append((concept,c[1]))
					set_concepts.append(concept);
	return list_concepts

'''def evaluate_concept_phrases(directory, window_size=10, concept_or_not_thresh=2, concept_relevance_thresh=8, section_occurns_thresh=2):
	transcripts = listdir(directory)
	lec_nos = [int(re.sub('[^\d]','',i)) for i in transcripts]
	transcripts = [x for (y, x) in sorted(zip(lec_nos, transcripts))]
	print 'Evaluating concept phrases on', len(transcripts), 'documents:'
	concept_scores = {}
	concept_relations = {}
	for transcript_num in range(len(transcripts)):
		print transcripts[transcript_num]
		fd = open(directory+'/'+transcripts[transcript_num])
		string = fd.read()
		fd.close()
		concepts = candidate_concept_phrases(string, concept_or_not_thresh) #[([w1,w2,...],[idx1,idx2,...])]
		concept_words = [' '.join(i[0]) for i in concepts]
		concept_lengths = [len(i[0]) for i in concepts]
		concept_indices = [i[1] for i in concepts]
		concept_relations = co_occurrence_analysis(string, concept_words, concept_lengths, concept_indices, concept_relations, window_size)
		occurns = [len(i[1]) for i in concepts]
		score = [0 for i in range(len(concepts))]
		keys = dict(get_text_rank(string, -1))
		for i in range(len(concepts)):
			for j in concepts[i][0]:
				word = SNOW.stem(LEMMATE.lemmatize(j))
				if word in keys:
					score[i] = max(score[i],keys[word])
		for i in range(len(concept_words)):
			if concept_words[i] in concept_scores:
				concept_scores[concept_words[i]] = (max(concept_scores[concept_words[i]][0], score[i]), concept_scores[concept_words[i]][1]+[(transcript_num,occurns[i])])
			else:
				concept_scores[concept_words[i]] = (score[i], [(transcript_num, occurns[i])])
	#compute related concepts
	for key, val in concept_relations.iteritems():
		for word in val.keys():
			if len(val[word])<section_occurns_thresh:
				val.pop(word)
			else:
				if not any([i>=concept_relevance_thresh for i in val[word]]):
					val.pop(word)
	for word in concept_relations.keys():
		if len(concept_relations[word]) == 0:
			concept_relations.pop(word)
	concept_scores = [(k, v[0], v[1]) for k, v in concept_scores.iteritems()]
	concept_scores = sorted(concept_scores,key=lambda x:x[1],reverse=True)
	concepts_for_lecs = [[[],[],0,0] for i in range(len(transcripts))]
	for i in concept_scores:
		if i[0] in concept_relations:
			concepts_for_lecs[i[2][0][0]][1].append([i[0],i[1],i[2][0][1]])
			concepts_for_lecs[i[2][0][0]][3] += i[2][0][1]
			for j in range(1,len(i[2])):
				concepts_for_lecs[i[2][j][0]][0].append([i[0],i[1],i[2][j][1]])
				concepts_for_lecs[i[2][j][0]][2] += i[2][j][1]
	for i in range(len(transcripts)):
		for j in range(len(concepts_for_lecs[i][0])):
			concepts_for_lecs[i][0][j][2] /= concepts_for_lecs[i][2]*1.0
		for j in range(len(concepts_for_lecs[i][1])):
			concepts_for_lecs[i][1][j][2] /= concepts_for_lecs[i][3]*1.0
	pickle.dump((concept_scores, concept_relations, concepts_for_lecs),open('data/'+directory+'_concept_phrases.pickle','w'))
	return (concept_scores, concept_relations, concepts_for_lecs)'''
	
def evaluate_concept_phrases(directory, concept_occurns_thresh=5, concept_score_thresh=5.0, cut=0): #outputs prereq and outcome concepts of every document in the given directory, along with the concept scores and weights
	transcripts = listdir(directory)
	lec_nos = [int(re.sub('[^\d]','',i)) for i in transcripts]
	transcripts = [x for (y, x) in sorted(zip(lec_nos, transcripts))]
	print 'Evaluating concept phrases on', len(transcripts), 'documents:'
	prereq_concept_scrs = []
	outcome_concepts = {}
	for transcript_num in range(len(transcripts)-cut):
		print transcripts[transcript_num]
		fd = open(directory+'/'+transcripts[transcript_num])
		string = fd.read()
		fd.close()
		concepts = candidate_concept_phrases(string, concept_occurns_thresh) #[([w1,w2,...],[idx1,idx2,...])]
		#pprint(concepts)
		concept_words = [' '.join(i[0]) for i in concepts]
		num_of_occrns = [len(i[1]) for i in concepts]
		text_rank_scr = [0 for i in range(len(concepts))]
		keys = dict(get_text_rank(string, -1))
		for i in range(len(concepts)):
			for j in concepts[i][0]:
				word = SNOW.stem(LEMMATE.lemmatize(j))
				if word in keys:
					text_rank_scr[i] = max(text_rank_scr[i], keys[word])
		to_remove = [i for i in range(len(text_rank_scr)) if text_rank_scr[i]<concept_score_thresh]
		for i in range(len(to_remove)):
			concepts.pop(to_remove[i]-i)
			concept_words.pop(to_remove[i]-i)
			num_of_occrns.pop(to_remove[i]-i)
			text_rank_scr.pop(to_remove[i]-i)
		prereq_concepts = {}
		for i in range(len(concept_words)):
			word = concept_words[i]
			prereq_concepts[word] = (text_rank_scr[i], num_of_occrns[i])
			if word in outcome_concepts:
				if outcome_concepts[word][0] < text_rank_scr[i]:
					outcome_concepts[word] = (text_rank_scr[i], transcript_num)
			else:
				outcome_concepts[word] = (text_rank_scr[i], transcript_num)
		prereq_concept_scrs.append(prereq_concepts)
	transcript_concepts = [[set(), set()] for i in range(len(transcripts))]
	for i in range(len(transcripts)-cut):
		for key in prereq_concept_scrs[i].keys():
			if outcome_concepts[key][1]>=i:
				prereq_concept_scrs[i].pop(key)
		transcript_concepts[i][0] = set(prereq_concept_scrs[i].keys())
	for key, value in outcome_concepts.iteritems():
		transcript_concepts[value[1]][1].add(key)
	wts = [[float(0) for i in range(len(transcripts))] for i in range(len(transcripts))]
	for i in range(len(transcripts)-cut):
		num_occurns = sum([val[1] for val in prereq_concept_scrs[i].values()])
		for j in range(i):
			prereq_outcome_int = list(transcript_concepts[i][0] & transcript_concepts[j][1])
			if len(prereq_outcome_int)==0:
				continue
			for k in prereq_outcome_int:
				wts[i][j] += float(prereq_concept_scrs[i][k][0]*prereq_concept_scrs[i][k][1])/num_occurns
			wts[i][j] *= float(len(prereq_outcome_int))/len(transcript_concepts[i][0])
	pickle.dump((transcript_concepts, prereq_concept_scrs, wts),open('data/'+directory+'_concept_phrases_'+str(concept_score_thresh)+'.pickle','w'))
	for i in range(len(transcripts)-cut):
		pprint(transcript_concepts[i])
	return (transcript_concepts, prereq_concept_scrs, wts)

'''def ilp (concept_phrase_file, beta=0):
	data = pickle.load(open(concept_phrase_file))
	num = len(data[2])
	wts = [[0.0 for i in range(len(data[2]))] for i in range(num)]
	concept_sets = [(set([j[0] for j in i[0]]), set([j[0] for j in i[1]])) for i in data[2]]
	for i in range(num):
		for j in range(i):
			prereq_outcome_int = concept_sets[j][1] & concept_sets[i][0]
			if len(prereq_outcome_int)==0:
				continue
			concept_relevances = 0.0
			for k in range(len(data[2][i][0])):
				if data[2][i][0][k][0] in prereq_outcome_int:
					concept_relevances += data[2][i][0][k][1]*data[2][i][0][k][2] #textrank_score*num_occurns
			wts[i][j] = concept_relevances*len(prereq_outcome_int)/len(concept_sets[i][0])
	hier_sets = [set() for i in range(num)]
	for n in range(2,num):
		lp = LpProblem('minimal_video_lecture_sequencing_'+str(n), LpMaximize)
		var = []
		for i in range(n): # variables
			var.append(LpVariable('x'+str(i), 0, 1, LpInteger))
		norm_wt = sum([wts[n][i] for i in range(n)])*1.0
		lp += sum([var[i]*((beta*wts[n][i]/norm_wt)-1+beta) for i in range(n)]) # objective function
		for i in range(1,n): # constraints
			norm_wt = sum([wts[i][j] for j in range(i)])*1.0
			lp += sum([wts[i][j]*var[j]/norm_wt for j in range(i)]) - (1-beta)*var[i] >= 0
		print lp
		lp.solve(GLPK(msg=False))
		print 'Lecture', n+1, 'Max value:', value(lp.objective)
		for v in lp.variables():
			print v.name, v.varValue
			if (v.varValue==1):
				hier_sets[n].add(int(v.name[1:])+1)
	return compare_hierarchies(hier_sets)'''

def non_optimal_ordering(concept_phrase_file): #after prereq/outcome concept annotation, does naive lecture selection if an outcome concept of lecture is the prerequisite ocncept of the target lecture
	data = pickle.load(open(concept_phrase_file))
	num = len(data[0])
	hier_sets = [set() for i in range(num)]
	for i in range(num):
		hier_sets[i].add(i+1)
		for j in range(i):
			if len(data[0][j][1] & data[0][i][0])>0:
				hier_sets[i].add(j+1)
	return compare_hierarchies(hier_sets)

def grid_search_non_opt_ord(): #grid-search over the TextRank threshold. The higher the thresh, the fewer the number of concepts.
	results = []
	for i in range(1,13):
		results.append(non_optimal_ordering('data/transcripts_concept_phrases_'+str(i)+'.pickle'))
	results = np.transpose(np.asarray(results))
	labels = ['precision', 'recall', 'f1_score', 'corr_coeff', 'accuracy']
	x_param = [i for i in range(1,13)]
	for i in range(5):
		plt.plot(x_param, results[i], label=labels[i])
	plt.legend(title='performance measures')
	plt.xlabel('TextRank thresholding score')
	plt.ylabel('measure')
	plt.title('Performance of Non-ILP Method, across varying TextRank thresholding score')
	plt.savefig('non_ilp_ordering.png')

def ilp (concept_phrase_file, beta=0.8, alpha=0.1): #ILP formulation of the problem. ignore alpha, same as beta for the current implementation
	data = pickle.load(open(concept_phrase_file))
	wts = data[2]
	#pprint(wts)
	#pprint(data[0])
	num = len(wts)
	hier_sets = [set() for i in range(num)]
	for n in range(2, num):
		lp = LpProblem('minimal_video_lecture_sequencing_'+str(n), LpMaximize)
		var = []
		for i in range(n): # variables
			var.append(LpVariable('x'+str(i), 0, 1, LpInteger))
		norm_wt = sum([wts[n][i] for i in range(n)])*1.0
		if norm_wt==0:
			continue
		lp += sum([var[i]*((beta*wts[n][i]/norm_wt)-1+beta) for i in range(n)]) # objective function
		for i in range(1,n): # constraints
			norm_wt = sum([wts[i][j] for j in range(i)])*1.0
			if norm_wt==0:
				continue
			lp += sum([wts[i][j]*var[j]/norm_wt for j in range(i)]) - alpha*var[i] >= 0
		#print lp
		lp.solve(GLPK(msg=False))
		#print 'Lecture', n+1, 'Max value:', value(lp.objective)
		for v in lp.variables():
			#print v.name, v.varValue
			if (v.varValue==1):
				hier_sets[n].add(int(v.name[1:])+1)
		hier_sets[n].add(n+1)
	return compare_hierarchies(hier_sets)
	
def grid_search_ilp (): #grid-search over the learning burden beta
	alphas = [0.1*i for i in range(11)]
	max_fscore = 0
	max_alpha = alphas[0]
	max_result = []
	print '=Grid search for ILP derived Ordering='
	for j in alphas:
		print 'alpha =', j
		result = ilp('data/transcripts_concept_phrases_4.pickle', j, j)

		if (result[2]>max_fscore):
			max_alpha = j
			max_fscore = result[2]
			max_result = result[:]
	return (max_alpha, max_result)

#x = grid_search_ilp()
#print 'Best result:', x
#x = non_optimal_ordering('data/transcripts_concept_phrases.pickle')
#grid_search_non_opt_ord()