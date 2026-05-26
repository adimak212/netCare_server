from __future__ import annotations

from typing import Dict, List

from src.algorithm.version2.domain.pattern import Pattern
from src.algorithm.version2.domain.demand_vector import DemandVector
from src.algorithm.version2.domain.resources import Resources


class PatternGenerator:
    """
    Generates valid packing patterns for a given rack/bin type.

    Improvements:
    - DFS/backtracking instead of hard-coded nested loops
    - early pruning when capacity is exceeded
    - dynamic per-branch upper bounds based on remaining capacity
    - pruning of weak / dominated patterns
    """

    ITEM_ORDER = ["pc", "switch", "router", "controller"]

    def __init__(self, templates: Dict[str, Resources], bin_templates: Dict[str, Dict]):
        self.templates = templates
        self.bin_templates = bin_templates

    def generate_for_bin_type(self, bin_type: str) -> List[Pattern]:
        rack_cfg = self.bin_templates[bin_type]

        rack_resources = Resources(
            u=rack_cfg["u"],
            watt=rack_cfg["watt"],
            cost=rack_cfg["cost"],
            ports=rack_cfg["ports"],
        )

        item_types = [item for item in self.ITEM_ORDER if item in self.templates]

        patterns: List[Pattern] = []

        self._dfs_generate_patterns(
            bin_type=bin_type,
            rack_resources=rack_resources,
            item_types=item_types,
            index=0,
            current_counts=DemandVector(pc=0, switch=0, router=0, controller=0),
            current_resources=Resources(),
            patterns=patterns,
        )

        patterns = self._prune_exact_duplicates(patterns)
        patterns = self._prune_dominated_patterns(patterns)
        patterns = [p for p in patterns if self._is_pattern_useful(p)]
        patterns.sort(key=self._pattern_score, reverse=True)

        return patterns

    def _dfs_generate_patterns(
        self,
        bin_type: str,
        rack_resources: Resources,
        item_types: List[str],
        index: int,
        current_counts: DemandVector,
        current_resources: Resources,
        patterns: List[Pattern],
    ) -> None:
        if not current_resources.fits_in(rack_resources):
            return
        if index == len(item_types):
            if current_counts.total_items() == 0:
                return
            pattern = Pattern(
                bin_type=bin_type,
                counts=current_counts,
                total_resources=current_resources,
                bin_capacity=rack_resources,
            )

            if self._is_pattern_useful(pattern):
                patterns.append(pattern)
            return
        item_name = item_types[index]
        template = self.templates[item_name]

        max_qty = self._max_feasible_given_remaining_capacity(
            item_name=item_name,
            rack_resources=rack_resources,
            used_resources=current_resources,
        )
        for qty in range(max_qty + 1):
            next_counts = DemandVector(
                pc=current_counts.pc,
                switch=current_counts.switch,
                router=current_counts.router,
                controller=current_counts.controller,
            )
            self._set_count(next_counts, item_name, self._get_count(next_counts, item_name) + qty)

            next_resources = current_resources + (template * qty)

            if not next_resources.fits_in(rack_resources):
                break

            self._dfs_generate_patterns(
                bin_type=bin_type,
                rack_resources=rack_resources,
                item_types=item_types,
                index=index + 1,
                current_counts=next_counts,
                current_resources=next_resources,
                patterns=patterns,
            )

    def _max_feasible_given_remaining_capacity(
        self,
        item_name: str,
        rack_resources: Resources,
        used_resources: Resources,
    ) -> int:
        """
        Compute the tightest upper bound for the current item type
        based on remaining rack capacity in this DFS branch.
        """
        item = self.templates[item_name]

        remaining_u = max(rack_resources.u - used_resources.u, 0)
        remaining_watt = max(rack_resources.watt - used_resources.watt, 0)
        remaining_ports = max(rack_resources.ports - used_resources.ports, 0)
        remaining_cost = max(rack_resources.cost - used_resources.cost, 0)

        bounds = []

        if item.u > 0:
            bounds.append(remaining_u // item.u)

        if item.watt > 0:
            bounds.append(remaining_watt // item.watt)

        if item.ports > 0:
            bounds.append(remaining_ports // item.ports)

        if item.cost > 0 and rack_resources.cost > 0:
            bounds.append(remaining_cost // item.cost)

        if not bounds:
            return 0

        return int(min(bounds))

    def _compute_resources(self, counts: DemandVector) -> Resources:
        total = Resources()

        if counts.pc > 0 and "pc" in self.templates:
            total += self.templates["pc"] * counts.pc

        if counts.switch > 0 and "switch" in self.templates:
            total += self.templates["switch"] * counts.switch

        if counts.router > 0 and "router" in self.templates:
            total += self.templates["router"] * counts.router

        if counts.controller > 0 and "controller" in self.templates:
            total += self.templates["controller"] * counts.controller

        return total

    def _is_pattern_useful(
        self,
        pattern: Pattern,
    ) -> bool:

        util=pattern.utilization_ratios()

        avg_util=(
            util["u"]+
            util["watt"]+
            util["ports"]
        )/3.0

        spread=max(util.values())-min(util.values())

        total_items=pattern.total_items()

        if total_items<=0:
            return False

        if avg_util<0.08:
            return False

        if spread>0.85:
            return False

        counts=pattern.counts

        non_zero=sum([
            1 if counts.pc>0 else 0,
            1 if counts.switch>0 else 0,
            1 if counts.router>0 else 0,
            1 if counts.controller>0 else 0,
        ])

        if non_zero==1 and total_items>4:
            return False

        dominant_share=max(
            counts.pc,
            counts.switch,
            counts.router,
            counts.controller,
        )/max(total_items,1)

        if dominant_share>0.90:
            return False

        if counts.pc>0 and counts.switch==0:
            return False

        return True
    def _pattern_score(self, pattern: Pattern) -> float:
        """
        Score patterns for solver-friendly ordering.
        """
        util = pattern.utilization_ratios()

        util_score = (
            util["u"] * 4.0 +
            util["watt"] * 2.5 +
            util["ports"] * 3.0
        )

        counts = pattern.counts
        covered_dimensions = sum([
            1 if counts.pc > 0 else 0,
            1 if counts.switch > 0 else 0,
            1 if counts.router > 0 else 0,
            1 if counts.controller > 0 else 0,
        ])

        dimension_bonus = covered_dimensions * 0.75

        total_items = max(pattern.total_items(), 1)
        dominant_share = max(
            counts.pc,
            counts.switch,
            counts.router,
            counts.controller,
        ) / total_items

        balance_bonus = (1.0 - dominant_share) * 2.0
        item_mix_bonus = min(total_items, 12) * 0.08

        return util_score + dimension_bonus + balance_bonus + item_mix_bonus

    def _prune_exact_duplicates(self, patterns: List[Pattern]) -> List[Pattern]:
        unique: Dict[str, Pattern] = {}

        for p in patterns:
            sig = p.signature()
            existing = unique.get(sig)

            if existing is None:
                unique[sig] = p
                continue

            if self._pattern_score(p) > self._pattern_score(existing):
                unique[sig] = p

        return list(unique.values())

    def _prune_dominated_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """
        Pattern A is dominated by Pattern B if:
        - B provides at least as many items of every type
        - B consumes no more resources
        - and B is strictly better somewhere
        """
        kept: List[Pattern] = []

        for candidate in patterns:
            dominated = False

            for other in patterns:
                if candidate is other:
                    continue

                if self._dominates(other, candidate):
                    dominated = True
                    break

            if not dominated:
                kept.append(candidate)

        return kept

    def _dominates(self, a: Pattern, b: Pattern) -> bool:
        a_counts = a.counts
        b_counts = b.counts

        a_res = a.total_resources
        b_res = b.total_resources

        counts_not_worse = (
            a_counts.pc >= b_counts.pc and
            a_counts.switch >= b_counts.switch and
            a_counts.router >= b_counts.router and
            a_counts.controller >= b_counts.controller
        )

        resources_not_worse = (
            a_res.u <= b_res.u and
            a_res.watt <= b_res.watt and
            a_res.ports <= b_res.ports and
            a_res.cost <= b_res.cost
        )

        strictly_better_somewhere = (
            a_counts.pc > b_counts.pc or
            a_counts.switch > b_counts.switch or
            a_counts.router > b_counts.router or
            a_counts.controller > b_counts.controller or
            a_res.u < b_res.u or
            a_res.watt < b_res.watt or
            a_res.ports < b_res.ports or
            a_res.cost < b_res.cost
        )

        return counts_not_worse and resources_not_worse and strictly_better_somewhere

    def _get_count(self, counts: DemandVector, item_name: str) -> int:
        if item_name == "pc":
            return counts.pc
        if item_name == "switch":
            return counts.switch
        if item_name == "router":
            return counts.router
        if item_name == "controller":
            return counts.controller
        raise ValueError(f"Unknown item type: {item_name}")

    def _set_count(self, counts: DemandVector, item_name: str, value: int) -> None:
        if item_name == "pc":
            counts.pc = value
            return
        if item_name == "switch":
            counts.switch = value
            return
        if item_name == "router":
            counts.router = value
            return
        if item_name == "controller":
            counts.controller = value
            return
        raise ValueError(f"Unknown item type: {item_name}")