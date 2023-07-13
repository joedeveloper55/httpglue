import psycopg
import psycopg.rows

from models.widgets import Widget


class WidgetStore:
    def __init__(self, db_conn_pool):
        self._db_conn_pool = db_conn_pool

    def _query_db(self, sql, params={}, fetch_items=False):
        with self._db_conn_pool.connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as curs:
                curs.execute(sql, params)
                if fetch_items:
                    return curs.fetchall()

    def _db_row_to_widget(self, row):
        return Widget.from_dict(row)

    def get_widget(self, w_id):
        results = self._query_db(
            """
            SELECT id,
                   name,
                   description
              FROM public.widgets
             WHERE id = %(w_id)s;
            """,
            {'w_id': w_id},
            fetch_items=True
        )
        if len(results) == 0:
            raise LookupError('couldn\'t find widget')
        return self._db_row_to_widget(results[0])

    def put_widget(self, w):
        self._query_db(
            """
            INSERT INTO public.widgets
                 VALUES (%(id)s, %(name)s, %(description)s)
            ON CONFLICT (id)
                     DO
                        UPDATE SET name = %(name)s,
                                   description = %(description)s;
            """,
            {
                'id': w.id,
                'name': w.name,
                'description': w.description
            }
        )

    def del_widget(self, w_id):
        self._query_db(
            """
            DELETE FROM public.widgets
                    WHERE id = %(id)s;
            """,
            {'id': w_id}
        )

    def get_widgets(self):
        results = self._query_db(
            """
            SELECT id,
                   name,
                   description
              FROM public.widgets;
            """,
            fetch_items=True
        )
        return [
            self._db_row_to_widget(row)
            for row in results
        ]

    def put_widgets(self, ws):
        self.del_widgets()

        with self._db_conn_pool.connection() as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as curs:
                curs.executemany(
                    """
                    INSERT INTO public.widgets
                         VALUES (%(id)s, %(name)s, %(description)s)
                    ON CONFLICT (id)
                             DO
                                UPDATE SET name = %(name)s,
                                           description = %(description)s;
                    """,
                    (w.to_dict() for w in ws)
                )

    def del_widgets(self):
        self._query_db(
            """
            DELETE FROM public.widgets;
            """
        )
