from typing import List, Dict, Tuple, Set
from models.automaton import Transition, StudentAutomaton, ReferenceAutomaton
from itertools import product, permutations
from typing import Final
from models.transition import OutputSignal
from models.hint import HintLevel
from models.responses import VerificationResult


class AutomatonService():

    _INPUT_SIGNALS = ["00", "01", "10", "11"]

    _DEFAULT_SEQUENCE_LENGTH: Final[int] = 5

    _ERROR_LIMIT_MINIMAL: Final[int] = 3
    _ERROR_LIMIT_DETAILED: Final[int] = 5

    _Y_EQUATION_MIN_LENGTH: Final[int] = 3
    _Y_EQUATION_TRANSITION_BITS = 2  # Длина битовой комбинации перехода (x1x2)
    
    # Префикс для имён состояний эталона
    _REFERENCE_STATE_PREFIX = "S"

    @staticmethod
    def _build_transition_map(
        transitions: List[Transition],
    ) -> Dict[Tuple[str, str], Tuple[str, int]]:
        """Построение карты переходов.

        Args:
            transitions: Список переходов автомата.

        Returns:
            Словарь, отображающий (исходное_состояние, вход) в (целевое_состояние, выход).

        Example:
            >>> transitions = [Transition(from="0", to="1", on=["00", "11"], out=1)]
            >>> result = {("0", "00"): ("1", 1), ("0", "11"): ("1", 1)}
            
            >>> transitions = [Transition(from="S0", to="S1", on=["00"], out=1)]
            >>> result = {("S0", "00"): ("S1", 1)}
        """
        transition_map: Dict[Tuple[str, str], Tuple[str, int]] = {}
        
        for trans in transitions:
            for input_combo in trans.on:
                key = (trans.from_state, input_combo)
                transition_map[key] = (trans.to_state, trans.out)
        
        return transition_map

    @staticmethod
    def _build_transition_map_with_mapping(
        student: StudentAutomaton,
        mapping: Dict[str, str]
    ) -> Dict[Tuple[str, str], Tuple[str, int]]:
        """
        Строит карту переходов студента с применением маппинга состояний на эталонные имена.
        
        Пример:
            student.transitions = [Transition(from="0", to="1", on=["00"], out=1)]
            mapping = {"0": "S0", "1": "S1"}
            Результат: {
                ("S0", "00"): ("S1", 1)  # коды студента заменены на имена эталона
            }
        
        Args:
            student: Автомат студента
            mapping: Отображение кодов студента на имена эталона
            
        Returns:
            Словарь переходов с эталонными именами состояний
        """
        student_transitions: Dict[Tuple[str, str], Tuple[str, int]] = {}
        
        for trans in student.transitions:
            student_from = mapping.get(trans.from_state)
            student_to = mapping.get(trans.to_state)
            
            if student_from is None or student_to is None:
                continue
            
            for input_combo in trans.on:
                key = (student_from, input_combo)
                student_transitions[key] = (student_to, trans.out)
        
        return student_transitions
    
    @staticmethod
    def _create_reverse_mapping(mapping: Dict[str, str]) -> Dict[str, str]:
        """
        Создаёт обратное отображение из прямого словаря.
        Parameters
        ----------
        mapping : Dict[str, str]
            Прямое отображение, где ключ - код студента, значение - эталонное имя состояния.
            Например: {"0": "S0", "1": "S1"}
        Returns
        -------
        Dict[str, str]
            Обратное отображение, где ключ - эталонное имя состояния, значение - код студента.
            Например: {"S0": "0", "S1": "1"}
        Examples
        --------
        >>> mapping = {"0": "S0", "1": "S1"}
        >>> AutomatonService._create_reverse_mapping(mapping)
        {"S0": "0", "S1": "1"}
        """
        return {v: k for k, v in mapping.items()}

    @staticmethod
    def generate_input_sequences(length: int = _DEFAULT_SEQUENCE_LENGTH) -> List[List[str]]:
        """
        Генерирует все возможные входные последовательности заданной длины.
        
        Args:
            length: Длина генерируемых последовательностей
            
        Returns:
            Список входных последовательностей, где каждая последовательность - список входов ("00", "01", "10", "11")
        """
        return [list(seq) for seq in product(AutomatonService._INPUT_SIGNALS, repeat=length)]
    
    @staticmethod
    def simulate_automaton(
        transitions: List[Transition],
        initial_state: str,
        input_sequence: List[str]
    ) -> Tuple[List[int], List[str]]:
        """
            Симулирует работу автомата на заданной входной последовательности.
            Args:
                transitions (List[Transition]): Список переходов автомата.
                initial_state (str): Начальное состояние автомата.
                input_sequence (List[str]): Входная последовательность символов для обработки.
            Returns:
                Tuple[List[int], List[str]]: Кортеж из двух элементов:
                    - List[int]: Список выходных сигналов автомата.
                    - List[str]: Список состояний автомата (включая начальное).
            Note:
                Если переход для текущего состояния и входного символа не определен,
                автомат остается в текущем состоянии и выдает выходной сигнал 0.
        """
        transition_map = AutomatonService._build_transition_map(transitions)
        
        current_state = initial_state
        outputs = []
        states = [current_state]
        
        for input_combo in input_sequence:
            key = (current_state, input_combo)
            
            if key not in transition_map:
                # Переход не определен - остаемся в текущем состоянии с выходом 0
                outputs.append(OutputSignal.ZERO)
                states.append(current_state)
            else:
                next_state, output = transition_map[key]
                outputs.append(output)
                current_state = next_state
                states.append(current_state)
        
        return outputs, states
    
    @staticmethod
    def _verify_with_mapping(
        student: StudentAutomaton,
        reference: ReferenceAutomaton,
        mapping: Dict[str, str]
    ) -> bool:
        """
        Проверяет, соответствует ли автомат студента эталонному автомату с использованием заданного отображения состояний.
        
        Этот метод проверяет, эквивалентен ли автомат студента эталонному автомату,
        когда состояния студента сопоставлены в соответствии с предоставленным словарем отображения.
        
        Args:
            student (StudentAutomaton): Автомат студента для проверки.
            reference (ReferenceAutomaton): Эталонный автомат для сравнения.
            mapping (Dict[str, str]): Словарь, отображающий имена состояний студента на имена эталонных состояний.
        
        Returns:
            bool: True, если автомат студента соответствует эталонному автомату с заданным отображением,
            False в противном случае.
        
        Проверка выполняет две проверки:
            1. Все переходы из эталонного автомата должны присутствовать в автомате студента
               с соответствующими целевыми состояниями и выходными значениями (после применения отображения).
            2. Автомат студента не должен содержать дополнительных переходов, которых нет
               в эталонном автомате.
        
        Example:
            Эталон: S0-[00]->S1(out=1)
            Студент: 0-[00]->1(out=1)
            mapping = {"0": "S0", "1": "S1"}
            Результат: True (структуры идентичны)
            
            Если бы у студента был 0-[00]->1(out=0), результат: False (разные выходы)
        """
        # Карты переходов
        ref_transitions = AutomatonService._build_transition_map(reference.transitions)
        student_transitions = AutomatonService._build_transition_map_with_mapping(student, mapping)
        
        # Проверка 1: Все переходы эталона должны присутствовать у студента
        for key, (ref_to, ref_output) in ref_transitions.items():
            if key not in student_transitions:
                return False
            
            student_to, student_output = student_transitions[key]
            if student_to != ref_to or student_output != ref_output:
                return False
        
        # Проверка 2: У студента не должно быть лишних переходов
        for key in student_transitions:
            if key not in ref_transitions:
                return False
        
        return True
    
    @staticmethod
    def find_state_mapping(
        student: StudentAutomaton,
        reference: ReferenceAutomaton
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Пытается найти валидное отображение между кодами состояний студента и эталонными состояниями.

        Args:
            student: Автомат студента
            reference: Эталонный автомат
            
        Returns:
            Кортеж (is_valid, mapping), где mapping = {код_состояния_студента: имя_эталонного_состояния}
        """
        if len(student.state_codes) != len(reference.state_codes):
            return False, {}
        
        # Пробуем все возможные перестановки
        for perm in permutations(reference.state_codes):
            mapping = {student.state_codes[i]: state_name for i, state_name in enumerate(perm)}
            
            if AutomatonService._verify_with_mapping(student, reference, mapping):
                return True, mapping
        
        return False, {}
    
    @staticmethod
    def _format_missing_transition_error(
        hint_level: HintLevel,
        student_state_code: str,
        input_val: str,
        expected_to_code: str,
        expected_output: int
    ) -> str:
        """
        Форматирует сообщение об ошибке отсутствующего перехода в автомате.

        Args:
            hint_level (HintLevel): Уровень детализации подсказки (без подсказок, легкие подсказки или полные подсказки).
            student_state_code (str): Код состояния, из которого отсутствует переход.
            input_val (str): Входное значение, для которого отсутствует переход.
            expected_to_code (str): Ожидаемый код состояния, в которое должен вести переход.
            expected_output (int): Ожидаемое выходное значение для перехода.

        Returns:
            str: Отформатированное сообщение об ошибке с учетом указанного уровня подсказок.
                - При NO_HINTS: общее сообщение без деталей
                - При LIGHT_HINTS: сообщение с указанием состояния и входа
                - При FULL_HINTS: полное сообщение с ожидаемым состоянием и выходом
        """
        if hint_level == HintLevel.NO_HINTS:
            return "Отсутствует один или несколько переходов"
        elif hint_level == HintLevel.LIGHT_HINTS:
            return f"Отсутствует переход из состояния {student_state_code} при входе {input_val}"
        else:  # hint_level == HintLevel.FULL_HINTS
            return (
                f"Отсутствует переход из состояния {student_state_code} при входе {input_val}. "
                f"Ожидается: переход в состояние {expected_to_code} с выходом {expected_output}"
            )
    
    @staticmethod
    def _format_wrong_transition_error(
        hint_level: HintLevel,
        student_state_code: str,
        input_val: str,
        actual_to_code: str,
        actual_output: int,
        expected_to_code: str,
        expected_output: int
    ) -> str:
        """
        Форматирует сообщение об ошибке неверного перехода автомата в зависимости от уровня подсказок.

        Args:
            hint_level (HintLevel): Уровень детализации подсказок для студента.
            student_state_code (str): Код состояния, из которого выполняется переход.
            input_val (str): Входное значение, при котором произошел переход.
            actual_to_code (str): Код состояния, в которое фактически произошел переход.
            actual_output (int): Фактическое выходное значение перехода.
            expected_to_code (str): Код состояния, в которое ожидался переход.
            expected_output (int): Ожидаемое выходное значение перехода.

        Returns:
            str: Отформатированное сообщение об ошибке с учетом уровня подсказок:
                - NO_HINTS: базовое сообщение без деталей
                - LIGHT_HINTS: сообщение с указанием состояния и входного значения
                - FULL_HINTS: полное сообщение с фактическими и ожидаемыми значениями
        """
        if hint_level == HintLevel.NO_HINTS:
            return "Обнаружен неверный переход"
        elif hint_level == HintLevel.LIGHT_HINTS:
            return f"Неверный переход из состояния {student_state_code} при входе {input_val}"
        else:  # hint_level == HintLevel.FULL_HINTS
            return (
                f"Неверный переход из состояния {student_state_code} при входе {input_val}. "
                f"Получено: переход в {actual_to_code} с выходом {actual_output}. "
                f"Ожидается: переход в {expected_to_code} с выходом {expected_output}"
            )
    
    @staticmethod
    def _format_extra_transition_error(
        hint_level: HintLevel,
        student_state_code: str,
        input_val: str,
        actual_to_code: str,
        actual_output: int
    ) -> str:
        """
        Форматирует сообщение об ошибке для лишнего перехода в автомате.
        Метод создает текст сообщения об ошибке, когда в автомате
        обнаружен переход, которого не должно быть в эталонном автомате.
        Уровень детализации сообщения зависит от параметра hint_level.
        Args:
            hint_level (HintLevel): Уровень детализации подсказок в сообщении об ошибке.
                - NO_HINTS: минимальная информация
                - LIGHT_HINTS: базовая информация о переходе
                - FULL_HINTS: полная информация о переходе
            student_state_code (str): Код состояния, из которого идет лишний переход.
            input_val (str): Входное значение, при котором происходит переход.
            actual_to_code (str): Код состояния, в которое ведет лишний переход.
            actual_output (int): Выходное значение, которое генерирует лишний переход.
        Returns:
            str: Отформатированное сообщение об ошибке лишнего перехода.
        Examples:
            >>> _format_extra_transition_error(HintLevel.NO_HINTS, "0", "11", "1", 0)
            "Обнаружен лишний переход"
            >>> _format_extra_transition_error(HintLevel.LIGHT_HINTS, "0", "11", "1", 0)
            "Лишний переход из состояния 0 при входе 11"
            >>> _format_extra_transition_error(HintLevel.FULL_HINTS, "0", "11", "1", 0)
        """
        if hint_level == HintLevel.NO_HINTS:
            return "Обнаружен лишний переход"
        elif hint_level == HintLevel.LIGHT_HINTS:
            return f"Лишний переход из состояния {student_state_code} при входе {input_val}"
        else:  # hint_level == HintLevel.FULL_HINTS
            return (
                f"Лишний переход из состояния {student_state_code} при входе {input_val} "
                f"в состояние {actual_to_code} с выходом {actual_output} (не должен существовать)"
            )

    @staticmethod
    def _check_graph_structure(
        student: StudentAutomaton,
        reference: ReferenceAutomaton,
        mapping: Dict[str, str],
        hint_level: HintLevel = HintLevel.NO_HINTS
    ) -> Tuple[bool, List[str]]:
        """
        Проверяет структуру графа переходов и формирует список ошибок.
        
        Выполняет три проверки:
            1. Все переходы из эталона должны быть у студента
            2. Выходы на соответствующих переходах должны совпадать
            3. У студента не должно быть лишних переходов
        
        Пример работы (hint_level=3):
            Эталон: S0-[00]->S1(out=1)
            Студент: 0-[00]->0(out=0)  # неверное целевое состояние и выход
            mapping = {"0": "S0", "1": "S1"}
            
            Ошибка: "Неверный переход из состояния 0 при входе 00. 
                     Получено: переход в 0 с выходом 0. 
                     Ожидается: переход в 1 с выходом 1"
        
        Args:
            student: Автомат студента
            reference: Эталонный автомат
            mapping: Отображение кодов студента на имена эталона
            hint_level: Уровень подсказок (1-без деталей, 2-место ошибки, 3-полная информация)
            
        Returns:
            Tuple[успех, список_текстовых_ошибок]
        """
        errors = []
        
        # Строим карты переходов
        ref_transitions = AutomatonService._build_transition_map(reference.transitions)
        student_transitions = AutomatonService._build_transition_map_with_mapping(student, mapping)
        reverse_mapping = AutomatonService._create_reverse_mapping(mapping)
        
        # Проверка 1: Все переходы эталона должны присутствовать у студента
        for key, (ref_to, ref_output) in ref_transitions.items():
            from_state, input_val = key
            student_state_code = reverse_mapping.get(from_state, "?")
            
            if key not in student_transitions:
                # Переход полностью отсутствует
                ref_to_code = reverse_mapping.get(ref_to, "?")
                error = AutomatonService._format_missing_transition_error(
                    hint_level, student_state_code, input_val, ref_to_code, ref_output
                )
                errors.append(error)
            else:
                # Переход есть, но проверяем корректность целевого состояния и выхода
                student_to, student_output = student_transitions[key]
                if student_to != ref_to or student_output != ref_output:
                    actual_state_code = reverse_mapping.get(student_to, "?")
                    ref_to_code = reverse_mapping.get(ref_to, "?")
                    error = AutomatonService._format_wrong_transition_error(
                        hint_level, student_state_code, input_val,
                        actual_state_code, student_output,
                        ref_to_code, ref_output
                    )
                    errors.append(error)
        
        # Проверка 2: У студента не должно быть лишних переходов
        for key in student_transitions:
            if key not in ref_transitions:
                from_state, input_val = key
                student_to, student_output = student_transitions[key]
                student_state_code = reverse_mapping.get(from_state, "?")
                actual_state_code = reverse_mapping.get(student_to, "?")
                
                error = AutomatonService._format_extra_transition_error(
                    hint_level, student_state_code, input_val, actual_state_code, student_output
                )
                errors.append(error)
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def _collect_transitions_with_output_1(student: StudentAutomaton) -> Set[Tuple[str, str]]:
        """
        Собирает все переходы автомата студента, которые имеют выходной сигнал y=1.
        
        Метод проходит по всем переходам автомата и для каждого перехода с выходом 1
        добавляет в множество пары (исходное_состояние, входной_символ).
        
        Args:
            student (StudentAutomaton): Автомат студента, содержащий список переходов.
        
        Returns:
            Set[Tuple[str, str]]: Множество пар (код_состояния, входной_символ),
                где каждая пара представляет переход с выходным сигналом y=1.
        
        Example:
            >>> # Переход: из состояния "1" в состояние "2" при входах ["00", "11"] с выходом 1
            >>> trans = Transition(from_state="1", to_state="2", on_inputs=["00", "11"], output=1)
            >>> student = StudentAutomaton(transitions=[trans], ...)
            >>> result = _collect_transitions_with_output_1(student)
            >>> result
            {("1", "00"), ("1", "11")}
        """
        transitions_with_output_1: Set[Tuple[str, str]] = set()
        for trans in student.transitions:
            if trans.out == OutputSignal.ONE:
                for input_combo in trans.on:
                    transitions_with_output_1.add((trans.from_state, input_combo))
        return transitions_with_output_1
    
    @staticmethod
    def _parse_student_y_equation(
        y_equation: List[str],
        state_codes: List[str]
    ) -> Tuple[bool, Set[Tuple[str, str]], str]:
        """
        Парсит уравнение выхода (y-уравнение) студента.
        Разбирает каждый элемент y-уравнения на код состояния и биты перехода.
        Проверяет корректность формата элементов и существование состояний.

        Args:
            y_equation (List[str]): Список элементов y-уравнения в формате "состояние+переход".
            state_codes (List[str]): Список допустимых кодов состояний.
        Returns:
            Tuple[bool, Set[Tuple[str, str]], str]: Кортеж из трёх элементов:
                - bool: True, если парсинг успешен, False в противном случае.
                - Set[Tuple[str, str]]: Множество пар (код_состояния, биты_перехода).
                - str: Сообщение об ошибке (пустая строка, если ошибок нет).
        Examples:
            >>> _parse_student_y_equation(['a00', 'b01'], ['a', 'b'])
            (True, {('a', '00'), ('b', '01')}, '')
        """
        y_equation_terms: Set[Tuple[str, str]] = set()
        
        for term in y_equation:
            # Минимальная длина: 1 символ (состояние) + 2 символа (переход) = 3
            if len(term) < AutomatonService._Y_EQUATION_MIN_LENGTH:
                return False, set(), f"y_equation: элемент '{term}' слишком короткий"
            
            # Последние N символов - переход (x1x2)
            transition_bits = term[-AutomatonService._Y_EQUATION_TRANSITION_BITS:]
            # Всё остальное - код состояния
            state_code = term[:-AutomatonService._Y_EQUATION_TRANSITION_BITS]
            
            # Проверяем, что код состояния существует
            if state_code not in state_codes:
                return False, set(), f"y_equation: состояние '{state_code}' из элемента '{term}' не найдено в state_codes"
            
            y_equation_terms.add((state_code, transition_bits))
        
        return True, y_equation_terms, ""
    
    @staticmethod
    def _parse_reference_y_equation(
        y_equation: List[str],
        states: List[str]
    ) -> Set[Tuple[str, str]]:
        """
        Разбирает уравнение выхода Y для извлечения ссылок на состояния и переходов.
        Метод анализирует список термов уравнения выхода, выделяя те, которые начинаются
        с префикса состояния-ссылки. Для каждого такого терма извлекается имя состояния
        и биты перехода.
        Args:
            y_equation (List[str]): Список термов уравнения выхода для разбора.
            states (List[str]): Список допустимых имен состояний автомата.
        Returns:
            Set[Tuple[str, str]]: Множество кортежей, где каждый кортеж содержит:
                - имя состояния (str): имя состояния с префиксом
                - биты перехода (str): строка битов перехода
        Note:
            - Пропускаются термы, не начинающиеся с префикса состояния-ссылки
            - Пропускаются термы с недостаточной длиной (меньше минимальной)
            - Пропускаются термы, ссылающиеся на несуществующие состояния
            - Биты перехода извлекаются из конца терма (количество определяется константой)
        """
        ref_terms: Set[Tuple[str, str]] = set()
        
        for term in y_equation:
            if not term.startswith(AutomatonService._REFERENCE_STATE_PREFIX):
                continue

            rest = term[len(AutomatonService._REFERENCE_STATE_PREFIX):]  # Убираем префикс
            if len(rest) < AutomatonService._Y_EQUATION_MIN_LENGTH:  # Минимум: 1 цифра + 2 бита
                continue

            transition_bits = rest[-AutomatonService._Y_EQUATION_TRANSITION_BITS:]
            state_name = f"{AutomatonService._REFERENCE_STATE_PREFIX}{rest[:-AutomatonService._Y_EQUATION_TRANSITION_BITS]}"

            if state_name not in states:
                continue
            
            ref_terms.add((state_name, transition_bits))
        
        return ref_terms
    
    @staticmethod
    def _create_diagnostic_mapping(
        student: StudentAutomaton,
        reference: ReferenceAutomaton
    ) -> Dict[str, str]:
        """
        Args:
            student (StudentAutomaton): Автомат студента, содержащий коды состояний
                и начальное состояние для отображения
            reference (ReferenceAutomaton): Эталонный автомат, содержащий имена 
                состояний и начальное состояние для сопоставления
        Returns:
            Dict[str, str]: Словарь отображения кодов состояний студента на имена
                состояний эталонного автомата. Ключи - коды состояний студента,
                значения - имена состояний эталона
        """
        diagnostic_mapping = {student.initial_state: reference.initial_state}

        student_states_remaining = [code for code in student.state_codes if code != student.initial_state]
        ref_states_remaining = [s for s in reference.state_codes if s != reference.initial_state]

        for student_code, ref_state in zip(student_states_remaining, ref_states_remaining):
            diagnostic_mapping[student_code] = ref_state

        return diagnostic_mapping

    @staticmethod
    def _format_input_sequence(input_seq: List[str], up_to_step: int) -> str:
        """
        Форматирует входную последовательность для отображения в ошибке.

        Examples:
            input_seq = ["00", "11", "01"]\\
            up_to_step = 2\\
            Результат: "00→11"

        Args:
            input_seq: Полная входная последовательность
            up_to_step: Индекс последнего шага (включительно)

        Returns:
            Строка с форматированной последовательностью
        """
        return "→".join(input_seq[:up_to_step])

    @staticmethod
    def _get_error_limit(hint_level: HintLevel) -> int:
        """
        Возвращает максимальное количество ошибок для отображения в зависимости от уровня подсказок.

        Уровень 1: 3 ошибки (минимальная информация)
        Уровень 2-3: 5 ошибок (больше деталей)

        Args:
            hint_level: Уровень подсказок (1-3)

        Returns:
            Максимальное количество ошибок
        """
        return AutomatonService._ERROR_LIMIT_MINIMAL if hint_level == HintLevel.NO_HINTS else AutomatonService._ERROR_LIMIT_DETAILED

    
    @staticmethod
    def _format_y_equation_error(hint_level: HintLevel, detailed_error: str) -> List[str]:
        """
        Форматирует ошибку y_equation в зависимости от уровня подсказок.
        
        Пример:
            hint_level=1: ["Каноническое уравнение неправильное"]
            hint_level=2: ["Ошибка в каноническом уравнении y"]
            hint_level=3: ["В автомате есть переход с выходом y=1: ..."]
        
        Args:
            hint_level: Уровень подсказок (1-3)
            detailed_error: Детальное сообщение об ошибке
            
        Returns:
            Список с одним отформатированным сообщением об ошибке
        """
        if hint_level == HintLevel.NO_HINTS:
            return ["Каноническое уравнение неправильное"]
        elif hint_level == HintLevel.LIGHT_HINTS:
            return ["Ошибка в каноническом уравнении y"]
        else:  # hint_level == HintLevel.FULL_HINTS
            return [detailed_error]
    
    @staticmethod
    def _verify_y_equation(
        student: StudentAutomaton,
        reference: ReferenceAutomaton,
        state_mapping: Dict[str, str]
    ) -> Tuple[bool, str]:
        """
        Проверяет корректность канонического уравнения y_equation.
        
        Выполняет проверки:
            1. Формат y_equation корректен (парсинг успешен)
            2. Все термы из y_equation соответствуют переходам с out=1
            3. Все переходы с out=1 присутствуют в y_equation
            4. Количество термов совпадает с эталоном
            5. Термы (с учётом маппинга) совпадают с эталоном
        
        Пример работы:
            Студент: transitions с out=1: {("1", "00")}
                     y_equation: ["100"] → парсится в {("1", "00")}
                     ✅ Совпадает
            
            Студент: transitions с out=1: {("1", "00")}
                     y_equation: ["010"] → парсится в {("0", "10")}
                     ❌ Терм "010" не соответствует переходу с out=1
        
        Args:
            student: Автомат студента
            reference: Эталонный автомат
            state_mapping: Отображение кодов студента на имена эталона
            
        Returns:
            Tuple[корректно, сообщение_об_ошибке_или_пустая_строка]
        """
        # Проверка 1: Собираем переходы с выходом y=1 из автомата студента
        transitions_with_output_1 = AutomatonService._collect_transitions_with_output_1(student)
        
        # Проверка 2: Парсим y_equation студента
        valid, y_equation_terms, error_msg = AutomatonService._parse_student_y_equation(
            student.y_equation, student.state_codes
        )

        if not valid:
            return False, error_msg
        
        # Проверка 3: Все термы из y_equation должны соответствовать переходам с output=1
        for state_code, transition_bits in y_equation_terms:
            if (state_code, transition_bits) not in transitions_with_output_1:
                mapped_state = state_mapping.get(state_code, "?")
                return False, (
                    f"y_equation содержит терм '{state_code}{transition_bits}' "
                    f"(состояние {state_code} → {mapped_state}, вход {transition_bits}), "
                    f"но этот переход не имеет выхода y=1 в вашем автомате"
                )
        
        # Проверка 4: Все переходы с output=1 должны быть в y_equation
        for state_code, transition_bits in transitions_with_output_1:
            if (state_code, transition_bits) not in y_equation_terms:
                mapped_state = state_mapping.get(state_code, "?")
                return False, (
                    f"В автомате есть переход с выходом y=1: "
                    f"из состояния {state_code} ({mapped_state}) при входе {transition_bits}, "
                    f"но этот терм отсутствует в y_equation"
                )
        
        # Проверка 5: Сравниваем с эталонным y_equation
        ref_terms = AutomatonService._parse_reference_y_equation(
            reference.y_equation, reference.state_codes
        )
        
        # Проверка 5a: Количество термов должно совпадать
        if len(y_equation_terms) != len(ref_terms):
            return False, (
                f"Количество термов в y_equation не совпадает с эталоном: "
                f"у вас {len(y_equation_terms)}, ожидается {len(ref_terms)}"
            )
        
        # Проверка 5b: Применяем маппинг и сравниваем множества
        mapped_student_terms: Set[Tuple[str, str]] = set()
        for state_code, transition_bits in y_equation_terms:
            mapped_state = state_mapping.get(state_code)
            if mapped_state:
                mapped_student_terms.add((mapped_state, transition_bits))
        
        if mapped_student_terms != ref_terms:
            return False, (
                "y_equation не соответствует эталону. "
                "Проверьте, что вы указали все переходы с выходом y=1"
            )
        
        return True, ""
    
    @staticmethod
    def verify_automaton(
        student: StudentAutomaton,
        reference: ReferenceAutomaton,
        test_length: int = 5
    ) -> VerificationResult:
        """
        Проверяет автомат студента против эталонного.
        
        Args:
            student: Отправленный автомат студента
            reference: Эталонный (правильный) автомат
            test_length: Длина тестовых последовательностей
            
        Returns:
            VerificationResult со статусом успеха и деталями ошибок
        """
        hint_level: HintLevel = student.hint_level
        
        # Шаг 1: Попытка найти валидное отображение состояний
        mapping_found, state_mapping = AutomatonService.find_state_mapping(student, reference)
        
        if not mapping_found:
            # Создаём диагностическое отображение для анализа ошибок
            diagnostic_mapping = AutomatonService._create_diagnostic_mapping(student, reference)
            
            # Проверим структуру с этим отображением для получения детальных ошибок
            _, graph_errors = AutomatonService._check_graph_structure(
                student, reference, diagnostic_mapping, hint_level
            )
            
            # Формируем сообщение в зависимости от уровня подсказок
            if hint_level == HintLevel.NO_HINTS:
                message = "Граф автомата неверный"
                # Ограничиваем ошибки до минимального лимита
                errors_to_show = graph_errors[:AutomatonService._ERROR_LIMIT_MINIMAL] if graph_errors else []
            else:
                message = "Граф автомата неверный"
                # Ограничиваем ошибки до детального лимита
                errors_to_show = graph_errors[:AutomatonService._ERROR_LIMIT_DETAILED] if graph_errors else []
                if len(graph_errors) > AutomatonService._ERROR_LIMIT_DETAILED:
                    errors_to_show.append(f"... и ещё {len(graph_errors) - AutomatonService._ERROR_LIMIT_DETAILED} ошибок")

            return VerificationResult(
                success=False,
                message=message,
                errors=errors_to_show,
                test_sequences_count=0
            )
        
        # Шаг 2: Генерация тестовых последовательностей
        test_sequences = AutomatonService.generate_input_sequences(test_length)
        
        # Шаг 3: Запуск симуляций и сравнение выходов
        error_messages: List[str] = []
        
        for _, input_seq in enumerate(test_sequences):
            # Симуляция эталона
            ref_outputs, _ = AutomatonService.simulate_automaton(
                reference.transitions,
                reference.initial_state,
                input_seq
            )
            
            # Симуляция автомата студента
            student_outputs, _ = AutomatonService.simulate_automaton(
                student.transitions,
                student.initial_state,
                input_seq
            )
            
            # Сравнение выходов
            error_limit = AutomatonService._get_error_limit(hint_level)
            
            for step, (ref_out, stud_out) in enumerate(zip(ref_outputs, student_outputs)):
                if ref_out != stud_out:
                    input_str = AutomatonService._format_input_sequence(input_seq, step + 1)
                    
                    if hint_level == HintLevel.NO_HINTS:
                        # Уровень 1: просто сообщаем о наличии ошибки
                        error_messages.append("Обнаружена ошибка в выходной последовательности")
                    elif hint_level == HintLevel.LIGHT_HINTS:
                        # Уровень 2: указываем шаг и входную последовательность
                        error_messages.append(
                            f"Ошибка на шаге {step + 1}, вход: {input_str}"
                        )
                    else:  # hint_level == HintLevel.FULL_HINTS
                        # Уровень 3: полная информация
                        error_messages.append(
                            f"Ошибка на шаге {step + 1}, вход: {input_str}. "
                            f"Получено: выход={stud_out}, ожидается: выход={ref_out}"
                        )
                    
                    # Ограничиваем количество ошибок
                    if len(error_messages) >= error_limit:
                        break
            
            if len(error_messages) >= error_limit:
                break
        
        test_sequences_count = len(test_sequences)
        
        if error_messages:
            return VerificationResult(
                success=False,
                message="Автомат работает неправильно",
                errors=error_messages,
                test_sequences_count=test_sequences_count
            )
        
        # Шаг 4: Проверка канонического уравнения y_equation
        y_equation_valid, y_equation_error = AutomatonService._verify_y_equation(
            student, reference, state_mapping
        )
        
        if not y_equation_valid:
            y_errors = AutomatonService._format_y_equation_error(hint_level, y_equation_error)
            
            return VerificationResult(
                success=False,
                message="Граф автомата верный, но каноническое уравнение неправильное",
                errors=y_errors,
                test_sequences_count=test_sequences_count
            )
        
        return VerificationResult(
            success=True,
            message="Автомат верный! Все проверки пройдены.",
            state_mapping=state_mapping,
            errors=[],
            test_sequences_count=test_sequences_count
        )
