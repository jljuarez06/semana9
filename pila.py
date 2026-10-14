class Stack:
    """Implementa una pila LIFO con capacidad limitada."""

    def __init__(self, capacity=10):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("La capacidad debe ser un entero.")

        if not 1 <= capacity <= 20:
            raise ValueError("La capacidad debe estar entre 1 y 20.")

        self.capacity = capacity
        self._items = []

    def is_empty(self):
        return len(self._items) == 0

    def is_full(self):
        return len(self._items) >= self.capacity

    def push(self, item):
        """Agrega un elemento al tope."""
        if self.is_full():
            return False

        self._items.append(item)
        return True

    def pop(self):
        """Elimina y devuelve el elemento del tope."""
        if self.is_empty():
            return None

        return self._items.pop()

    def peek(self):
        """Consulta el tope sin eliminarlo."""
        if self.is_empty():
            return None

        return self._items[-1]

    def show(self):
        """Devuelve los elementos desde el tope hasta la base."""
        return list(reversed(self._items))

    def clear(self):
        """Vacía la pila."""
        self._items.clear()

    def __len__(self):
        return len(self._items)