from src.algorithm.version2.domain import (
    Resources,
    ItemTemplate,
    DemandVector,
    Pattern,
    UserPreferences,
)


def main():
    rack = Resources(u=12, watt=1500, cost=20000, ports=24)
    pc = Resources(u=1, watt=50, cost=200, ports=1)
    switch = Resources(u=2, watt=120, cost=1500, ports=8)

    #("Resources add:", (pc + switch).as_dict())
    #("Fits in rack:", (pc + switch).fits_in(rack))

    template = ItemTemplate(
        key="pc",
        size=pc,
        allowed_bin_types=("rack",),
    )
    #("Template fits rack:", template.fits_bin_type("rack"))

    demand1 = DemandVector(pc=10, switch=3, router=1)
    demand2 = DemandVector(pc=2, switch=1, router=0)

    #("Demand add:", (demand1 + demand2).as_dict())
    #("Demand sub:", (demand1 - demand2).as_dict())
    #("Demand covers:", demand1.covers(demand2))

    pattern = Pattern(
        bin_type="rack",
        counts=DemandVector(pc=4, switch=2, router=1),
        total_resources=Resources(u=12, watt=540, cost=8200, ports=20),
    )
    #("Pattern:", pattern.as_dict())

    prefs = UserPreferences(
        pcs=20,
        scalability=100,
        redundancy=50,
        cost=90,
    )
    #("Preferences normalized:", prefs.normalized_importance())


if __name__ == "__main__":
    main()