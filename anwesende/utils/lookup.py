from django.db.models import Lookup
import django.db.models as djdm


@djdm.CharField.register_lookup
class ILike(Lookup):
    lookup_name = 'ilike'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return '%s ILIKE %s' % (lhs, rhs), params
