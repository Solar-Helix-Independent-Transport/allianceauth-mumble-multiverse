# Standard Library
import logging

# Django
from django.conf import settings
from django.db import models

# Alliance Auth
from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCorporationInfo,
    EveFactionInfo,
)

logger = logging.getLogger(__name__)


class MumbleverseServerQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user.has_perm('mumbleverse.basic_access'):
            logger.debug(f'Returning No Servers for No Access Perm {user}')
            return self.none()

        try:
            main_character = user.profile.main_character
            assert main_character

            # superusers/global get all visible
            if user.is_superuser or user.has_perm('mumbleverse.global_access'):
                logger.debug(f'Returning all Servers for Global Perm {user}')
                return self

            # build all accepted queries and then OR them
            queries = []
            # States access everyone has a state
            queries.append(
                models.Q(
                    state_access=user.profile.state
                )
            )
            # Groups access, is ok if no groups.
            queries.append(
                models.Q(
                    group_access__in=user.groups.all()
                )
            )
            # ONLY on main char from here down
            # Character access
            queries.append(
                models.Q(
                    character_access=main_character
                )
            )
            # Corp access
            try:
                queries.append(
                    models.Q(
                        corporation_access=EveCorporationInfo.objects.get(
                            corporation_id=main_character.corporation_id
                        )
                    )
                )
            except EveCorporationInfo.DoesNotExist:
                pass
            # Alliance access if part of an alliance
            try:
                if main_character.alliance_id:
                    queries.append(
                        models.Q(
                            alliance_access=EveAllianceInfo.objects.get(
                                alliance_id=main_character.alliance_id
                            )
                        )
                    )
            except EveAllianceInfo.DoesNotExist:
                pass
            # Faction access if part of a faction
            try:
                if main_character.faction_id:
                    queries.append(
                        models.Q(
                            faction_access=EveFactionInfo.objects.get(
                                faction_id=main_character.faction_id
                            )
                        )
                    )
            except EveFactionInfo.DoesNotExist:
                pass

            logger.debug(
                f"{len(queries)} queries for {main_character}'s visible characters.")

            if settings.DEBUG:
                logger.debug(queries)

            # filter based on "OR" all queries
            query = queries.pop()
            for q in queries:
                query |= q
            return self.filter(query)
        except AssertionError:
            logger.debug(
                'User %s has no main character. Nothing visible.' % user)
            return self.none()


class MumbleverseServerManager(models.Manager):
    """Manager for MumbleverseServer"""

    def get_queryset(self):
        return MumbleverseServerQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)
