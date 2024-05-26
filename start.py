from big_ol_pile_of_manim_imports import *

import scipy.integrate

OUTPUT_DIRECTORY = "bayes/part1"

HYPOTHESIS_COLOR = YELLOW
NOT_HYPOTHESIS_COLOR = GREY
EVIDENCE_COLOR1 = BLUE_C
EVIDENCE_COLOR2 = BLUE_E
NOT_EVIDENCE_COLOR1 = GREY
NOT_EVIDENCE_COLOR2 = GREY_D

#


def get_bayes_formula(expand_denominator=False):
    t2c = {
        "{H}": HYPOTHESIS_COLOR,
        "{\\neg H}": NOT_HYPOTHESIS_COLOR,
        "{E}": EVIDENCE_COLOR1,
    }
    isolate = ["P", "\\over", "=", "\\cdot", "+"]

    tex = "P({H} | {E}) = {P({H}) P({E} | {H}) \\over "
    if expand_denominator:
        tex += "P({H}) P({E} | {H}) + P({\\neg H}) \\cdot P({E} | {\\neg H})}"
    else:
        tex += "P({E})}"

    formula = TexMobject(
        tex,
        tex_to_color_map=t2c,
        isolate=isolate,
    )

    formula.posterior = formula[:6]
    formula.prior = formula[8:12]
    formula.likelihood = formula[13:19]

    if expand_denominator:
        pass
        formula.denom_prior = formula[20:24]
        formula.denom_likelihood = formula[25:31]
        formula.denom_anti_prior = formula[32:36]
        formula.denom_anti_likelihood = formula[37:42]
    else:
        formula.p_evidence = formula[20:]

    return formula


class BayesDiagram(VGroup):
    CONFIG = {
        "height": 2,
        "square_style": {
            "fill_color": GREY_D,
            "fill_opacity": 1,
            "stroke_color": WHITE,
            "stroke_width": 2,
        },
        "rect_style": {
            "stroke_color": WHITE,
            "stroke_width": 1,
            "fill_opacity": 1,
        },
        "hypothesis_color": HYPOTHESIS_COLOR,
        "not_hypothesis_color": NOT_HYPOTHESIS_COLOR,
        "evidence_color1": EVIDENCE_COLOR1,
        "evidence_color2": EVIDENCE_COLOR2,
        "not_evidence_color1": NOT_EVIDENCE_COLOR1,
        "not_evidence_color2": NOT_EVIDENCE_COLOR2,
        "prior_rect_direction": DOWN,
    }

    def __init__(self, prior, likelihood, antilikelihood, **kwargs):
        super().__init__(**kwargs)
        square = Square(side_length=self.height)
        square.set_style(**self.square_style)

        # Create all rectangles
        h_rect, nh_rect, he_rect, nhe_rect, hne_rect, nhne_rect = [
            square.copy().set_style(**self.rect_style)
            for x in range(6)
        ]

        # Add as attributes
        self.square = square
        self.h_rect = h_rect  # Hypothesis
        self.nh_rect = nh_rect  # Not hypothesis
        self.he_rect = he_rect  # Hypothesis and evidence
        self.hne_rect = hne_rect  # Hypothesis and not evidence
        self.nhe_rect = nhe_rect  # Not hypothesis and evidence
        self.nhne_rect = nhne_rect  # Not hypothesis and not evidence

        # Stretch the rectangles
        for rect in h_rect, he_rect, hne_rect:
            rect.stretch(prior, 0, about_edge=LEFT)
        for rect in nh_rect, nhe_rect, nhne_rect:
            rect.stretch(1 - prior, 0, about_edge=RIGHT)

        he_rect.stretch(likelihood, 1, about_edge=DOWN)
        hne_rect.stretch(1 - likelihood, 1, about_edge=UP)
        nhe_rect.stretch(antilikelihood, 1, about_edge=DOWN)
        nhne_rect.stretch(1 - antilikelihood, 1, about_edge=UP)

        # Color the rectangles
        h_rect.set_fill(self.hypothesis_color)
        nh_rect.set_fill(self.not_hypothesis_color)
        he_rect.set_fill(self.evidence_color1)
        hne_rect.set_fill(self.not_evidence_color1)
        nhe_rect.set_fill(self.evidence_color2)
        nhne_rect.set_fill(self.not_evidence_color2)

        # Add them
        self.hypothesis_split = VGroup(h_rect, nh_rect)
        self.evidence_split = VGroup(he_rect, hne_rect, nhe_rect, nhne_rect)

        # Don't add hypothesis split by default
        self.add(self.square, self.hypothesis_split, self.evidence_split)
        self.square.set_opacity(0)
        self.hypothesis_split.set_opacity(0)

    def add_brace_attrs(self, buff=SMALL_BUFF):
        braces = self.braces = self.create_braces(buff)
        self.braces_buff = buff
        attrs = [
            "h_brace",
            "nh_brace",
            "he_brace",
            "hne_brace",
            "nhe_brace",
            "nhne_brace",
        ]
        for brace, attr in zip(braces, attrs):
            setattr(self, attr, brace)
        return self

    def create_braces(self, buff=SMALL_BUFF):
        kw = {
            "buff": buff,
            "min_num_quads": 1,
        }
        return VGroup(
            Brace(self.h_rect, self.prior_rect_direction, **kw),
            Brace(self.nh_rect, self.prior_rect_direction, **kw),
            Brace(self.he_rect, LEFT, **kw),
            Brace(self.hne_rect, LEFT, **kw),
            Brace(self.nhe_rect, RIGHT, **kw),
            Brace(self.nhne_rect, RIGHT, **kw),
        )

    def refresh_braces(self):
        if hasattr(self, "braces"):
            self.braces.become(
                self.create_braces(self.braces_buff)
            )
        return self

    def set_prior(self, new_prior):
        p = new_prior
        q = 1 - p
        full_width = self.square.get_width()

        left_rects = [self.h_rect, self.he_rect, self.hne_rect]
        right_rects = [self.nh_rect, self.nhe_rect, self.nhne_rect]

        for group, vect, value in [(left_rects, LEFT, p), (right_rects, RIGHT, q)]:
            for rect in group:
                rect.set_width(
                    value * full_width,
                    stretch=True,
                    about_edge=vect,
                )

        self.refresh_braces()
        return self

    def general_set_likelihood(self, new_likelihood, low_rect, high_rect):
        height = self.square.get_height()

        low_rect.set_height(
            new_likelihood * height,
            stretch=True,
            about_edge=DOWN,
        )
        high_rect.set_height(
            (1 - new_likelihood) * height,
            stretch=True,
            about_edge=UP,
        )
        self.refresh_braces()
        return self

    def set_likelihood(self, new_likelihood):
        self.general_set_likelihood(
            new_likelihood,
            self.he_rect,
            self.hne_rect,
        )
        return self

    def set_antilikelihood(self, new_antilikelihood):
        self.general_set_likelihood(
            new_antilikelihood,
            self.nhe_rect,
            self.nhne_rect,
        )
        return self

    def copy(self):
        return self.deepcopy()


class ProbabilityBar(VGroup):
    CONFIG = {
        "color1": BLUE_D,
        "color2": GREY_BROWN,
        "height": 0.5,
        "width": 6,
        "rect_style": {
            "stroke_width": 1,
            "stroke_color": WHITE,
            "fill_opacity": 1,
        },
        "include_braces": False,
        "brace_direction": UP,
        "include_percentages": True,
        "percentage_background_stroke_width": 2,
    }

    def __init__(self, p=0.5, **kwargs):
        super().__init__(**kwargs)
        self.add_backbone()
        self.add_p_tracker(p)
        self.add_bars()
        if self.include_braces:
            self.braces = always_redraw(lambda: self.get_braces())
            self.add(self.braces)
        if self.include_percentages:
            self.percentages = always_redraw(lambda: self.get_percentages())
            self.add(self.percentages)

    def add_backbone(self):
        backbone = Line()
        backbone.set_opacity(0)
        backbone.set_width(self.width)
        self.backbone = backbone
        self.add(backbone)

    def add_p_tracker(self, p):
        self.p_tracker = ValueTracker(p)

    def add_bars(self):
        bars = VGroup(Rectangle(), Rectangle())
        bars.set_height(self.height)
        colors = [self.color1, self.color2]
        for bar, color in zip(bars, colors):
            bar.set_style(**self.rect_style)
            bar.set_fill(color=color)

        bars.add_updater(self.update_bars)
        self.bars = bars
        self.add(bars)

    def update_bars(self, bars):
        vects = [LEFT, RIGHT]
        p = self.p_tracker.get_value()
        values = [p, 1 - p]
        total_width = self.backbone.get_width()
        for bar, vect, value in zip(bars, vects, values):
            bar.set_width(value * total_width, stretch=True)
            bar.move_to(self.backbone, vect)
        return bars

    def get_braces(self):
        return VGroup(*[
            Brace(
                bar,
                self.brace_direction,
                min_num_quads=1,
                buff=SMALL_BUFF,
            )
            for bar in self.bars
        ])

    def get_percentages(self):
        p = self.p_tracker.get_value()
        labels = VGroup(*[
            Integer(value, unit="\\%")
            for value in [
                np.floor(p * 100),
                100 - np.floor(p * 100),
            ]
        ])
        for label, bar in zip(labels, self.bars):
            label.set_height(0.75 * bar.get_height())
            min_width = 0.75 * bar.get_width()
            if label.get_width() > min_width:
                label.set_width(min_width)
            label.move_to(bar)
            label.set_stroke(
                BLACK,
                self.percentage_background_stroke_width,
                background=True
            )
        return labels

    def add_icons(self, *icons, buff=SMALL_BUFF):
        if hasattr(self, "braces"):
            refs = self.braces
        else:
            refs = self.bars

        for icon, ref in zip(icons, refs):
            icon.ref = ref
            icon.add_updater(lambda i: i.next_to(
                i.ref,
                self.brace_direction,
                buff=buff
            ))
        self.icons = VGroup(*icons)
        self.add(self.icons)


class Steve(SVGMobject):
    CONFIG = {
        "file_name": "steve",
        "fill_color": GREY,
        "sheen_factor": 0.5,
        "sheen_direction": UL,
        "stroke_width": 0,
        "height": 3,
        "include_name": True,
        "name": "Steve"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.include_name:
            self.add_name()

    def add_name(self):
        self.name = TextMobject(self.name)
        self.name.match_width(self)
        self.name.next_to(self, DOWN, SMALL_BUFF)
        self.add(self.name)


class Linda(Steve):
    CONFIG = {
        "file_name": "linda",
        "name": "Linda"
    }


class LibrarianIcon(SVGMobject):
    CONFIG = {
        "file_name": "book",
        "stroke_width": 0,
        "fill_color": GREY_B,
        "sheen_factor": 0.5,
        "sheen_direction": UL,
        "height": 0.75,
    }


class FarmerIcon(SVGMobject):
    CONFIG = {
        "file_name": "farming",
        "stroke_width": 0,
        "fill_color": GREEN_E,
        "sheen_factor": 0.5,
        "sheen_direction": UL,
        "height": 1.5,
    }


class PitchforkIcon(SVGMobject):
    CONFIG = {
        "file_name": "pitch_fork_and_roll",
        "stroke_width": 0,
        "fill_color": GREY_B,
        "sheen_factor": 0.5,
        "sheen_direction": UL,
        "height": 1.5,
    }


class Person(SVGMobject):
    CONFIG = {
        "file_name": "person",
        "height": 1.5,
        "stroke_width": 0,
        "fill_opacity": 1,
        "fill_color": GREY_B,
    }


class Librarian(Person):
    CONFIG = {
        "IconClass": LibrarianIcon,
        "icon_style": {
            "background_stroke_width": 5,
            "background_stroke_color": BLACK,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        icon = self.IconClass()
        icon.set_style(**self.icon_style)
        icon.match_width(self)
        icon.move_to(self.get_corner(DR), DOWN)
        self.add(icon)


class Farmer(Librarian):
    CONFIG = {
        "IconClass": FarmerIcon,
        "icon_style": {
            "background_stroke_width": 2,
        },
        "fill_color": GREEN,
    }


# Scenes


class Test(Scene):
    def construct(self):
        icon = FarmerIcon()
        icon.scale(2)
        self.add(icon)
        # self.add(get_submobject_index_labels(icon))


# class FullFormulaIndices(Scene):
#     def construct(self):
#         formula = get_bayes_formula(expand_denominator=True)
#         formula.set_width(FRAME_WIDTH - 1)
#         self.add(formula)
#         self.add(get_submobject_index_labels(formula))


class IntroduceFormula(Scene):
    def construct(self):
        formula = get_bayes_formula()
        print(formula[0])
        formula.save_state()
        formula.set_width(FRAME_WIDTH - 1)

        def get_formula_slice(*indices):
            return VGroup(*[formula[0][i] for i in indices])

        H_label = formula.get_part_by_tex("{H}")
        E_label = formula.get_part_by_tex("{E}")

        hyp_label = TextMobject("Hypothesis")
        hyp_label.set_color(HYPOTHESIS_COLOR)
        hyp_label.next_to(H_label, UP, LARGE_BUFF)

        evid_label = TextMobject("Evidence")
        evid_label.set_color(EVIDENCE_COLOR1)
        evid_label.next_to(E_label, DOWN, LARGE_BUFF)

        hyp_arrow = Arrow(hyp_label.get_bottom(), H_label.get_top(), buff=SMALL_BUFF)
        evid_arrow = Arrow(evid_label.get_top(), E_label.get_bottom(), buff=SMALL_BUFF)

        self.add(formula[:6])
        # self.add(get_submobject_index_labels(formula))
        # return
        self.play(
            FadeIn(hyp_label),
            GrowArrow(hyp_arrow),
            FadeIn(evid_label),
            GrowArrow(evid_arrow),
        )
        self.wait()

        # Prior
        self.play(
            ShowCreation(formula.get_part_by_tex("=")),
            #TransformFromCopy(
            #    get_formula_slice(0, 1, 2, 5),
            #    get_formula_slice(8, 9, 10, 11),
            #),
        )

        # Likelihood
        lhs_copy = formula[:6].copy()
        likelihood = formula[12:18]
        run_time = 1
        self.play(
            lhs_copy.next_to, likelihood, UP,
            run_time=run_time,
        )
        self.play(
            Swap(lhs_copy[2], lhs_copy[4]),
            run_time=run_time,
        )
        self.play(
            lhs_copy.move_to, likelihood,
            run_time=run_time,
        )

        # Evidence
        self.play(
            ShowCreation(formula.get_part_by_tex("\\over")),
            #TransformFromCopy(
            #    get_formula_slice(0, 1, 4, 5),
            #    get_formula_slice(19, 20, 21, 22),
            #),
        )
        self.wait()

        self.clear()
        self.play(
            formula.restore,
            formula.scale, 1.5,
            formula.to_edge, UP,
            FadeOut(VGroup(
                hyp_arrow, hyp_label,
                evid_arrow, evid_label,
            ))
        )


class StateGoal(PiCreatureScene, Scene):
    CONFIG = {
        "default_pi_creature_kwargs": {
            "color": BLUE_B,
            "height": 2,
        },

    }

    def construct(self):
        # Zoom to later
        you = self.pi_creature
        line = NumberLine(
            x_min=-2,
            x_max=12,
            include_tip=True
        )
        line.to_edge(DOWN, buff=1.5)
        line.to_edge(LEFT, buff=-0.5)

        you.next_to(line.n2p(0), UP)

        you_label = TextMobject("you")
        you_label.next_to(you, RIGHT, MED_LARGE_BUFF)
        you_arrow = Arrow(you_label.get_left(), you.get_right() + 0.5 * LEFT, buff=0.1)

        now_label = TextMobject("Now")
        later_label = TextMobject("Later")
        now_label.next_to(line.n2p(0), DOWN)
        later_label.next_to(line.n2p(10), DOWN)

        self.add(line, now_label)
        self.add(you)
        self.play(
            FadeIn(you_label, LEFT),
            GrowArrow(you_arrow),
            you.change, "pondering",
        )
        self.wait()
        you_label.add(you_arrow)
        self.play(
            you.change, "horrified",
            you.look, DOWN,
            you.next_to, line.n2p(10), UP,
            MaintainPositionRelativeTo(you_label, you),
            FadeIn(later_label, now_label.get_center()),
        )
        self.wait()

        # Add bubble
        bubble = you.get_bubble(
            height=4,
            width=6,
        )
        bubble.set_fill(opacity=0)
        formula = get_bayes_formula()
        bubble.position_mobject_inside(formula)

        self.play(
            you.change, "confused", bubble,
            ShowCreation(bubble),
        )
        self.play(FadeIn(formula))
        self.play(you.change, "hooray", formula)
        self.wait(2)

        # Show examples
        icons = VGroup(
            SVGMobject(file_name="science"),
            SVGMobject(file_name="robot"),
        )
        for icon in icons:
            icon.set_stroke(width=0)
            icon.set_fill(GREY)
            icon.set_sheen(1, UL)
            icon.set_height(1.5)
        icons[0].set_stroke(GREY, 3, background=True)
        gold = self.get_gold()
        icons.add(gold)

        icons.arrange(DOWN, buff=MED_LARGE_BUFF)
        icons.to_corner(UL)

        for icon in icons[:2]:
            self.play(
                Write(icon, run_time=2),
                you.change, "thinking", icon,
            )
        self.play(
            Blink(you),
            FadeOut(VGroup(
                line, now_label, later_label,
                you_label, you_arrow
            )),
        )
        self.play(
            FadeIn(gold, LEFT),
            you.change, "erm", gold,
        )
        self.play(Blink(you))

        # Brief Thompson description
        words = VGroup(
            TextMobject("1988").scale(1.5),
            TextMobject("Tommy Thompson\\\\and friends"),
        )
        words.arrange(DOWN, buff=0.75)

        ship = ImageMobject("ss_central_america")
        ship.set_width(4)
        ship.move_to(gold, DL)
        ship_title = TextMobject("SS Central America")
        ship_title.next_to(ship, UP)

        words.next_to(ship, RIGHT)

        self.play(
            FadeIn(words[0], LEFT),
            you.change, "tease", words,
            FadeOut(icons[:2]),
        )
        self.play(FadeIn(words[1], UP))
        self.wait()

        self.add(ship, gold)
        self.play(
            FadeIn(ship),
            gold.scale, 0.2,
            gold.move_to, ship,
        )
        self.play(FadeInFromDown(ship_title))
        self.play(you.change, "thinking", ship)

        amount = TexMobject("> \\$700{,}000{,}000")
        amount.scale(1.5)
        amount.next_to(ship, DOWN, MED_LARGE_BUFF)
        amount.to_edge(LEFT, buff=2)
        amount.set_color(YELLOW)

        gold_copy = gold.copy()
        self.play(
            gold_copy.scale, 3,
            gold_copy.next_to, amount, LEFT,
            FadeIn(amount),
        )
        self.play(Blink(you))
        self.wait()
        self.play(LaggedStartMap(
            FadeOutAndShift,
            Group(*words, ship_title, ship, gold, gold_copy, amount),
        ))

        # Levels of understanding
        # Turn bubble into level points
        level_points = VGroup(*[bubble.copy() for x in range(3)])
        for n, point in enumerate(level_points):
            point.set_width(0.5)
            point.set_height(0.5, stretch=True)
            point.add(*[
                point[-1].copy().scale(1.2**k)
                for k in range(1, n + 1)
            ])
            point[:3].scale(1.2**n, about_point=point[3].get_center())
            point.set_stroke(width=2)
            point.set_fill(opacity=0)
        level_points.arrange(DOWN, buff=LARGE_BUFF)

        title = TextMobject("Levels of understanding")
        title.scale(1.5)
        title.to_corner(UL)
        underline = Line()
        underline.match_width(title)
        underline.move_to(title, DOWN)
        title.add(underline)

        level_points.next_to(title, DOWN, buff=1.5)
        level_points.to_edge(LEFT)
        level_points.set_submobject_colors_by_gradient(GREEN, YELLOW, RED)

        self.remove(bubble)
        self.play(
            formula.to_corner, UR,
            FadeOut(you),
            *[
                ReplacementTransform(bubble.copy(), point)
                for point in level_points
            ],
        )
        self.play(Write(title, run_time=1))
        self.wait()

        # Write level 1
        level_labels = VGroup(
            TextMobject("What is it saying?"),
            TextMobject("Why is it true?"),
            TextMobject("When is it useful?"),
        )
        for lp, ll in zip(level_points, level_labels):
            ll.scale(1.25)
            ll.match_color(lp)
            ll.next_to(lp, RIGHT)

        formula_parts = VGroup(
            formula.prior,
            formula.likelihood,
            formula.p_evidence,
            formula.posterior,
        ).copy()
        formula_parts.generate_target()
        formula_parts.target.scale(1.5)
        formula_parts.target.arrange(DOWN, buff=LARGE_BUFF, aligned_edge=LEFT)
        formula_parts.target.next_to(formula, DOWN, buff=LARGE_BUFF)
        formula_parts.target.shift(3 * LEFT)

        equal_signs = VGroup(*[
            TextMobject("=").next_to(fp, RIGHT)
            for fp in formula_parts.target
        ])

        kw = {
            "tex_to_color_map": {
                "hypothesis": HYPOTHESIS_COLOR,
                "evidence": EVIDENCE_COLOR1,
            },
            "alignment": "",
        }
        meanings = VGroup(
            TextMobject("Probability a hypothesis is true\\\\(before any evidence)", **kw),
            TextMobject("Probability of seeing the evidence \\quad \\\\if the hypothesis is true", **kw),
            TextMobject("Probability of seeing the evidence", **kw),
            TextMobject("Probability a hypothesis is true\\\\given some evidence", **kw),
        )
        for meaning, equals in zip(meanings, equal_signs):
            meaning.scale(0.5)
            meaning.next_to(equals, RIGHT)

        self.play(
            FadeIn(level_labels[0], lag_ratio=0.1),
            MoveToTarget(formula_parts),
            LaggedStartMap(FadeInFrom, equal_signs, lambda m: (m, RIGHT)),
            LaggedStartMap(FadeIn, meanings),
        )
        self.wait()

        # Write level 2
        diagram = BayesDiagram(0.35, 0.5, 0.2, height=2.5)
        diagram.next_to(formula, DOWN, aligned_edge=LEFT)

        braces = VGroup(*[
            Brace(diagram.he_rect, vect, buff=SMALL_BUFF)
            for vect in [DOWN, LEFT]
        ])

        formula_parts.generate_target()
        formula_parts.target[:2].scale(0.5)
        formula_parts.target[0].next_to(braces[0], DOWN, SMALL_BUFF)
        formula_parts.target[1].next_to(braces[1], LEFT, SMALL_BUFF)

        pe_picture = VGroup(
            diagram.he_rect.copy(),
            TexMobject("+"),
            diagram.nhe_rect.copy()
        )
        pe_picture.arrange(RIGHT, buff=SMALL_BUFF)
        pe_picture.next_to(equal_signs[2], RIGHT)

        phe_picture = VGroup(
            diagram.he_rect.copy(),
            Line().match_width(pe_picture),
            pe_picture.copy(),
        )
        phe_picture.arrange(DOWN, buff=MED_SMALL_BUFF)
        phe_picture.next_to(equal_signs[3], RIGHT)

        pe_picture.scale(0.5, about_edge=LEFT)
        phe_picture.scale(0.3, about_edge=LEFT)

        self.play(
            FadeOut(meanings),
            FadeOut(equal_signs[:2]),
            MoveToTarget(formula_parts),
            FadeIn(diagram),
            LaggedStartMap(GrowFromCenter, braces),
            FadeIn(level_labels[1], lag_ratio=0.1),
            level_labels[0].set_opacity, 0.5,
        )
        self.play(
            TransformFromCopy(diagram.he_rect, pe_picture[0]),
            TransformFromCopy(diagram.nhe_rect, pe_picture[2]),
            FadeIn(pe_picture[1]),
        )
        self.play(
            TransformFromCopy(pe_picture, phe_picture[2]),
            TransformFromCopy(pe_picture[0], phe_picture[0]),
            ShowCreation(phe_picture[1])
        )
        self.wait()

        # Write level 3
        steve = Steve(height=3)
        steve.to_edge(RIGHT, buff=2)

        arrow = Arrow(level_points.get_bottom(), level_points.get_top(), buff=0)
        arrow.shift(0.25 * LEFT)

        self.play(
            LaggedStartMap(
                FadeOutAndShift,
                VGroup(
                    VGroup(diagram, braces, formula_parts[:2]),
                    VGroup(formula_parts[2], equal_signs[2], pe_picture),
                    VGroup(formula_parts[3], equal_signs[3], phe_picture),
                ),
                lambda m: (m, 3 * RIGHT),
            ),
            FadeIn(level_labels[2], lag_ratio=0.1),
            level_labels[1].set_opacity, 0.5,
        )
        self.wait()
        self.play(
            GrowArrow(arrow),
            level_points.shift, 0.5 * RIGHT,
            level_labels.shift, 0.5 * RIGHT,
            level_labels.set_opacity, 1,
        )
        self.wait()
        self.play(Write(steve, run_time=3))
        self.wait()

        # Transition to next scene
        self.play(
            steve.to_corner, UR,
            Uncreate(arrow),
            LaggedStartMap(
                FadeOutAndShift,
                VGroup(
                    title,
                    formula,
                    *level_points,
                    *level_labels,
                ),
                lambda m: (m, DOWN),
            ),
        )
        self.wait()

    def get_gold(self):
        gold = SVGMobject(file_name="gold_bars")[0]
        gold.set_stroke(width=0)
        gold.set_fill(GOLD)
        gold.set_sheen(0.5, UP)
        gold.flip(UP)
        gold_copy = gold.copy()
        gold_copy.shift(2 * OUT)

        rects = VGroup()
        for curve in CurvesAsSubmobjects(gold):
            p1 = curve.get_points()[0]
            p2 = curve.get_points()[-1]
            rect = Polygon(p1, p2, p2 + 2 * OUT, p1 + 2 * OUT)
            rect.match_style(gold)
            # rect.set_fill(GOLD)
            # rect.set_sheen(1, UL)
            rects.add(rect)
        rects.sort(lambda p: p[1])
        gold.add(*rects)
        gold.add(gold_copy)

        # gold = rects

        gold.rotate(2 * DEGREES, UP)
        gold.rotate(2 * DEGREES, RIGHT)
        gold.set_shade_in_3d(True)
        gold.set_height(1.5)
        gold.set_stroke(BLACK, 0.5)
        return 