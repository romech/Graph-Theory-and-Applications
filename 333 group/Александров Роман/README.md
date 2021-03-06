## Домашнее задание №1
### Граф дорог г. Чебоксары

### Задание №1
См. описание в файле "Пояснительная записка"

### Задание №2
Задача о поиске кратчайших путей от некоторой точки на карте до всех больниц.
* Реализации алгоритмов поиска кратчайшего пути расположены в файле `pathfinding_algorithms.py`.
* Пример выходных файлов, сравнительные показатели алгоритмов и визуализацию путей можно найти в папке `src/output`.
* Скрипт для запуска - `task2_demo.py`. Можно воспользоваться скомпилированной версией для Windows x64 в папке `build`.
	* для построения путей от заданной точки запустить с параметром: либо id точки, либо latitude longitude;
	* для запуска тестов сравнения алгоритмов на 100 равномерно распределённых точках - запуск с параметром `benchmark`;
	* для сравнения эвристических функций в алгоритме A* - запуск с параметром `astar`.

Всё алгоритмы в подавляющем большинстве случаев дают абсолютно одинаковый результат, поэтому программа строит на карте и в csv лишь путь с помощью алгоритма Дейкстры. Хотя изменить такое поведение в скрипте довольно просто.

### Задание №3
Задача коммивояжёра. Построение пути от случайной точки на карте (склада) через 10 больниц с возвратом назад.
* Реализации алгоритмов:
	* "Ближайшего соседа" `tsp_nn.py`,
	* "Имитации отжига" `tsp_sim_annealing.py`.
* Пример выходных файлов в папке `src/output`.
* Скрипт для запуска - `task3_demo.py`. Можно воспользоваться скомпилированной версией для Windows x64 в папке `build`. При запуске можно указать:
	* либо один параметр - номер вершины- склада,
	* либо 2 числа - координаты склада по широте и долготе.
