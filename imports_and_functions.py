import markovify
import random
import re
import pymorphy2
morph = pymorphy2.MorphAnalyzer()

def build_model(filename, newline=False, state_size=2):
    with open(filename, encoding='UTF-8') as f:
        text = f.read()
    if newline:
        model = markovify.NewlineText(text, state_size=state_size)
    else:
        model = markovify.Text(text, state_size=state_size)
    return model

def build_all_models_for_category(category='zakuski'):
    titles_model = build_model(f'{category}_titles_for_markovify_edaru.txt', newline=True, state_size=1)
    intros_model = build_model(f'{category}_intros_for_markovify_edaru.txt', newline=False, state_size=2)
    ingredients_model = build_model(f'{category}_ingredients_for_markovify_edaru.txt', newline=True, state_size=3)
    allsteps_model = build_model(f'{category}_allsteps_for_markovify_edaru.txt', newline=False, state_size=2)
    mainsteps_model = build_model(f'{category}_mainsteps_for_markovify_edaru.txt', newline=False, state_size=2)
    laststeps_model = build_model(f'{category}_laststeps_for_markovify_edaru.txt', newline=False, state_size=2)
    twolaststeps_model = build_model(f'{category}_twolaststeps_for_markovify_edaru.txt', newline=False, state_size=2)
    advice_model = build_model(f'{category}_advice_for_markovify_edaru.txt', newline=False, state_size=2)
    return {'titles_model' : titles_model, 'intros_model' : intros_model, 'ingredients_model' : ingredients_model, 
            'allsteps_model' : allsteps_model, 'mainsteps_model' : mainsteps_model, 'laststeps_model' : laststeps_model, 
            'twolaststeps_model' : twolaststeps_model, 'advice_model' : advice_model}

def build_all_the_models():
    full_dict = {}
    for category in ['zakuski', 'salads', 'soups', 'pies']:
        full_dict[category] = build_all_models_for_category(category)
    return full_dict

def pick_category():
    choice = input('Выберите категорию блюда из списка: супы, салаты, горячие закуски, пироги, рандом')
    if choice == 'супы':
        cat = 'soups'
    elif choice == 'салаты':
        cat = 'salads'
    elif choice in ['горячие закуски', 'закуски']:
        cat = 'zakuski'
    elif choice == 'пироги':
        cat = 'pies'
    elif choice == 'рандом':
        cat = choice
    else:
        print('Я вас не понял, попробуйте еще раз')
        pick_category()
    return cat
    
def pick_title(giant_model, cat):
    if cat != 'рандом':
        for _ in range(20):
            title = giant_model[cat]['titles_model'].make_sentence(test_output=True)
            print(f'{cat}\t{title}')
    else:
        for _ in range(20):
            categories = ['zakuski', 'salads', 'soups', 'pies']
            cat = random.choice(categories)
            title = giant_model[cat]['titles_model'].make_sentence(test_output=True)
            print(f'{cat}\t{title}')

    response = input('Скопируйте сюда строку с выбранным заголовком рецепта или напишите "нет", чтобы попробовать еще раз: ')
    if response == 'нет':
        pick_title(giant_model, cat)
    else:
        cat = response.split('\t')[0]
        chosen_title = response.split('\t')[1]
        return cat, chosen_title

def split_title_into_words(chosen_title):
    set_of_ingrs = set(chosen_title.split())
    for word in chosen_title.split():
        set_of_ingrs.add(word.lower())
        set_of_ingrs.add(word.capitalize())
    return set_of_ingrs

def get_ingredient_wordforms(set_of_ingrs):
    possible_wordforms_for_ingrs = set()
    for ingr in set_of_ingrs:
        butyavka = morph.parse(ingr)[0]
        for form in butyavka.lexeme:
            possible_wordforms_for_ingrs.add(form.word)
    possible_wordforms_for_ingrs.update(set_of_ingrs)
    low_and_cap = set()
    for wordform in possible_wordforms_for_ingrs:
        low_and_cap.add(wordform.lower())
        low_and_cap.add(wordform.capitalize())
    possible_wordforms_for_ingrs.update(low_and_cap)
    return possible_wordforms_for_ingrs

def produce_ingredients_from_title_first(full_dict, cat, possible_wordforms_for_ingrs):
    ingredient_list = []
    count = 0
    response = input('Логичнее или экспериментальнее?')
    if response == 'логичнее':
        response = False
    if response == 'экспериментальнее':
        response = True
    for wordform in possible_wordforms_for_ingrs:
        try:
            ingr = full_dict[cat]['ingredients_model'].make_sentence_with_start(wordform, strict=False, tries=10, test_output=response)
            if ingr:
                ingredient_list.append(ingr)
                print(f'{count}\t{ingr}')
                count += 1
        except:
            pass
    while len(ingredient_list) <= 15:
        ingr = full_dict[cat]['ingredients_model'].make_sentence(tries=10, test_output=response)
        if ingr:
            ingredient_list.append(ingr)
            print(f'{count}\t{ingr}')
            count += 1

    return ingredient_list

def modify_ingr_list(full_dict, ingredient_list, cat):
    response = ''
    response = input('Если вы не хотите ничего удалять, нажмите Enter. Если вы хотите убрать какие-то из ингредиентов, введите их номера через пробел')
    if response:
        indeces_to_delete = response.split(' ')
        for x in indeces_to_delete[::-1]:
            del ingredient_list[int(x)]
    response = input('Если вы не хотите ничего добавлять, нажмите Enter. Если вы хотите добавить какие-то ингредиенты, введите их названия через пробел')
    if response:
        new_ingr_words = set(response.split(' '))
        ingredient_list = add_more_ingrs_when_asked(full_dict, ingredient_list, new_ingr_words, cat)
        modify_ingr_list(full_dict, ingredient_list, cat)
    
    return ingredient_list

def add_more_ingrs_when_asked(full_dict, ingredient_list, set_of_ingrs, cat):
    count = len(ingredient_list)
    wordforms = get_ingredient_wordforms(set_of_ingrs)
    response = input('Логичнее или экспериментальнее?')
    if response == 'логичнее':
        response = False
    if response == 'экспериментальнее':
        response = True
    for wordform in wordforms:
        try:
            ingr = full_dict[cat]['ingredients_model'].make_sentence_with_start(wordform, strict=False, tries=10, test_output=response)
            if ingr:
                ingredient_list.append(ingr)
                print(f'{count}\t{ingr}')
                count += 1
        except:
            pass

    return ingredient_list

def get_forms_for_ingrs(ingredient_list):
    cases = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']
    nums = ['sing', 'plur']
    list_of_form_lists = []
    for ingr_line in ingredient_list:
        item_subset = set()
        item = ingr_line.split(' — ')[0]
        item = item.lower()
        words = item.split()
        for word in words:
            if morph.parse(word)[0].tag.POS == 'NOUN':
                item_subset.add(word)
                for case in cases:
                    for num in nums:
                        try:
                            item_subset.add(morph.parse(word)[0].inflect({case, num}).word)
                        except:
                            pass
        item_sublist = list(item_subset)
        item_sublist_cap = [x.capitalize() for x in item_sublist]
        item_sublist.extend(item_sublist_cap)
        list_of_form_lists.append(item_sublist)
    return list_of_form_lists

def produce_steps(full_dict, list_of_ingrs_form_lists, cat, model='mainsteps_model'):
    count = 0
    steps = []
    for sublist in list_of_ingrs_form_lists:
        for wordform in sublist:
            try:
                step = full_dict[cat][model].make_sentence_with_start(wordform, strict=False, tries=10,                                                                                                     test_output=False)
                if step:
                    steps.append(step)
                    print(f'{count}\t{step}')
                    count += 1
            except:
                pass
    response = input('Выберите те шаги, которые подходят к рецепту, и напишите их номера через пробел')
    if response:
        to_keep = response.split(' ')
        steps_kept = [steps[int(x)] for x in to_keep]

    return steps_kept

def produce_start_text(full_dict, chosen_title, list_of_ingrs_form_lists, cat, model='advice_model'):
    text_list = []
    for _ in range(len(re.findall(',', chosen_title))+1):
        chosen_title = re.sub(',', '', chosen_title)
    list_of_ingrs_form_lists.append(chosen_title.split())
    count = 0
    text_temp = []
    text_kept = ''
    for sublist in list_of_ingrs_form_lists:
        for wordform in sublist:
                try:
                    text = full_dict[cat][model].make_sentence_with_start(wordform, strict=False, tries=50, test_output=False)
                    if text:
                        text_temp.append(text)
                        print(f'{count}\t{text}')
                        count += 1
                except:
                    pass
    tip = 'совет' if 'advice' in model else 'вступление'
    response = input(f'Выберите те фрагменты, которые подходят, чтобы начать генерировать {tip} к рецепту, и напишите их номера через пробел')
    if response:
        to_keep = response.split(' ')
        text_kept = [text_temp[int(x)] for x in to_keep]
    else:
        text_temp = [full_dict[cat][model].make_sentence(tries=100, test_output=True) for _ in range(3)]
        for index, text in enumerate(text_temp):
            print(f'{index}\t{text}')
        response = input(f'Выберите те фрагменты, которые подходят, чтобы начать генерировать {tip} к рецепту, и напишите их номера через пробел')
        if response:
            to_keep = response.split(' ')
            text_kept = [text_temp[int(x)] for x in to_keep]

    return text_kept

def produce_text_based_on_prior_text(full_dict, text_kept, cat, model='advice_model'):
    nexts = []
    for sentence in text_kept:
        words = sentence.strip('.').split()
        for wordform in words:
            try:
                next_sentence = full_dict[cat][model].make_sentence_with_start(wordform, strict=False, tries=50,                                                                                                     test_output=True)
                if next_sentence:
                    response = input(f'Добавить это предложение? {next_sentence}')
                    if response == 'да':
                        nexts.append(next_sentence)
            except:
                pass
    if nexts:
        text_kept.extend(nexts)
        return text_kept
    else:
        if len(text_kept) < 2:
            try:
                next_sentence = full_dict[cat][model].make_sentence(tries=50,                                                                                                     test_output=True)
                if next_sentence:
                    response = input(f'Добавить это предложение? {next_sentence}')
                    if response == 'да':
                        text_kept.append(next_sentence)
            except:
                pass
        return text_kept

def print_beautifully(chosen_title, intro_text, ingredient_list, mainsteps, last_steps, advice_text):
    steps = mainsteps + last_steps
    print(f'{chosen_title}\n')

    for x in intro_text:
        print(x.capitalize(), end = ' ')
    print('\n')

    print('Ингредиенты:')
    for x in ingredient_list:
        print(x.capitalize())
    print('\n')

    print('Инструкция:')
    for x, step in enumerate(steps):
        print(f'{x + 1}. {step.capitalize()}')
    print('\n')

    print('Совет к рецепту:')
    for x in advice_text:
        print(x.capitalize(), end = ' ')
    print('\n')
