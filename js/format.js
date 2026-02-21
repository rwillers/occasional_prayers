(function () {
    const pageRoot = document.getElementById("content");
    const prayerContent = document.querySelector("[data-pagefind-body]");
    if (!pageRoot || !prayerContent) {
        return;
    }

    const controls = document.getElementById("format-controls");
    const languageControl = document.getElementById("language-modernization");
    const pronounControl = document.getElementById("pronouns");
    const toggleLanguageOriginal = document.getElementById("toggleLanguageOriginal");
    const toggleLanguageModern = document.getElementById("toggleLanguageModern");
    const toggleF = document.getElementById("toggleF");
    const toggleM = document.getElementById("toggleM");

    const PRONOUN_BASE_MARKUP = [
        { pattern: /<em>him<\/em>/gi, key: "obj", value: "him" },
        { pattern: /<em>his<\/em>/gi, key: "pos", value: "his" },
        { pattern: /<em>he<\/em>/gi, key: "sub", value: "he" },
        { pattern: /<em>himself<\/em>/gi, key: "ref", value: "himself" },
        { pattern: /<em>brother<\/em>/gi, key: "rel", value: "brother" },
    ];

    const PRONOUN_FORMS = {
        m: { obj: "him", pos: "his", sub: "he", ref: "himself", rel: "brother" },
        f: { obj: "her", pos: "her", sub: "she", ref: "herself", rel: "sister" },
        p: { obj: "them", pos: "their", sub: "they", ref: "themselves", rel: "siblings" },
    };

    const MODERNIZATION_PHRASE_REPLACEMENTS = {
        "art thou": "are you",
        "thou art": "you are",
        "which art": "which are",
        "who art": "who are",
        "thine they were": "they were yours",
        "thine alone": "yours alone",
        "thine is": "yours is",
        "is thine": "is yours",
        "are thine": "are yours",
        "thine ears": "your ears",
        "thine hand": "your hand",
        "thine apostles": "your apostles",
        "thine infinite": "your infinite",
        "thine almighty": "your almighty",
        "thine own": "your own",
    };

    // Conservative allowlist: only reviewed forms are modernized.
    const MODERNIZATION_WORD_REPLACEMENTS = {
        abidest: "abide",
        abideth: "abides",
        affordest: "afford",
        appeareth: "appears",
        availeth: "avails",
        bearest: "bear",
        becometh: "becomes",
        becommeth: "becomes",
        beholdest: "behold",
        believeth: "believes",
        belongeth: "belongs",
        biddest: "bid",
        bindest: "bind",
        blessest: "bless",
        bringest: "bring",
        broughtest: "brought",
        calleth: "calls",
        callest: "call",
        camest: "came",
        canst: "can",
        caredst: "cared",
        carest: "care",
        casteth: "casts",
        commandest: "command",
        commandedst: "commanded",
        commendeth: "commends",
        comest: "come",
        cometh: "comes",
        couldst: "could",
        declarest: "declare",
        delightest: "delight",
        deservest: "deserve",
        desirest: "desire",
        desireth: "desires",
        despisest: "despise",
        diddest: "did",
        didst: "did",
        disagreeth: "disagrees",
        displeaseth: "displeases",
        dividest: "divide",
        doest: "do",
        doeth: "does",
        dost: "do",
        doth: "does",
        drinketh: "drinks",
        dwellest: "dwell",
        dwelleth: "dwells",
        eateth: "eats",
        enablest: "enable",
        endureth: "endures",
        entrustest: "entrust",
        exaltest: "exalt",
        exalteth: "exalts",
        fadeth: "fades",
        failest: "fail",
        feedest: "feed",
        filleth: "fills",
        fillest: "fill",
        findeth: "finds",
        floweth: "flows",
        forgivest: "forgive",
        forgettest: "forget",
        forsaketh: "forsakes",
        gatherest: "gather",
        gavest: "gave",
        givest: "give",
        giveth: "gives",
        goest: "go",
        goeth: "goes",
        haddest: "had",
        hadst: "had",
        hast: "have",
        hath: "has",
        hearest: "hear",
        healest: "heal",
        holdest: "hold",
        inhabitest: "inhabit",
        intercedeth: "intercedes",
        judgest: "judge",
        knowest: "know",
        knoweth: "knows",
        leadeth: "leads",
        leaveth: "leaves",
        lettest: "let",
        lieth: "lies",
        liftest: "lift",
        livest: "live",
        liveth: "lives",
        lovest: "love",
        loveth: "loves",
        lurketh: "lurks",
        madest: "made",
        maist: "may",
        makest: "make",
        maketh: "makes",
        mayest: "may",
        mightest: "might",
        moveth: "moves",
        nourishest: "nourish",
        openest: "open",
        openeth: "opens",
        ordainest: "ordain",
        orderest: "order",
        ordereth: "orders",
        overcometh: "overcomes",
        passeth: "passes",
        perisheth: "perishes",
        pleaseth: "pleases",
        pointest: "point",
        preservest: "preserve",
        proceedeth: "proceeds",
        providest: "provide",
        pourest: "pour",
        pursueth: "pursues",
        putteth: "puts",
        reacheth: "reaches",
        receiveth: "receives",
        reignest: "reign",
        reigneth: "reigns",
        remaineth: "remains",
        rememberest: "remember",
        repentest: "repent",
        requirest: "require",
        resisteth: "resists",
        restest: "rest",
        riseth: "rises",
        rulest: "rule",
        runneth: "runs",
        saidst: "said",
        sanctifieth: "sanctifies",
        saveth: "saves",
        sayest: "say",
        scatterest: "scatter",
        seest: "see",
        seeth: "sees",
        seekest: "seek",
        sendest: "send",
        serveth: "serves",
        settest: "set",
        shalt: "will",
        sheddeth: "sheds",
        shineth: "shines",
        shinedst: "shined",
        shouldest: "should",
        shouldst: "should",
        showest: "show",
        shuttest: "shut",
        shutteth: "shuts",
        sittest: "sit",
        sitteth: "sits",
        sojourneth: "sojourns",
        soughtest: "sought",
        sparest: "spare",
        spreadest: "spread",
        standest: "stand",
        strengtheneth: "strengthens",
        sufferedst: "suffered",
        takest: "take",
        taketh: "takes",
        thee: "you",
        thirsteth: "thirsts",
        thou: "you",
        thy: "your",
        thyself: "yourself",
        thyselves: "yourselves",
        tookest: "took",
        turnest: "turn",
        understandeth: "understands",
        upliftest: "uplift",
        wandreth: "wanders",
        wast: "were",
        watchest: "watch",
        willest: "will",
        wilt: "will",
        workest: "work",
        worketh: "works",
        wouldest: "would",
        wouldst: "would",
        ye: "you",
        yieldeth: "yields",
    };

    function escapeRegex(value) {
        return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    function buildModernizationPatterns() {
        const patterns = [];

        const phraseEntries = Object.entries(MODERNIZATION_PHRASE_REPLACEMENTS).sort(
            function (a, b) {
                return b[0].length - a[0].length;
            },
        );
        for (const [source, replacement] of phraseEntries) {
            patterns.push({
                pattern: new RegExp(`\\b${escapeRegex(source)}\\b`, "gi"),
                replacement,
            });
        }

        const wordEntries = Object.entries(MODERNIZATION_WORD_REPLACEMENTS).sort(
            function (a, b) {
                return b[0].length - a[0].length;
            },
        );
        for (const [source, replacement] of wordEntries) {
            patterns.push({
                pattern: new RegExp(`\\b${escapeRegex(source)}\\b`, "gi"),
                replacement,
            });
        }

        return patterns;
    }

    const MODERNIZATION_PATTERNS = buildModernizationPatterns();

    function withCase(source, replacement) {
        if (source === source.toUpperCase()) {
            return replacement.toUpperCase();
        }
        if (source.charAt(0) === source.charAt(0).toUpperCase()) {
            return replacement.charAt(0).toUpperCase() + replacement.slice(1);
        }
        return replacement;
    }

    function applyNamePlaceholders(html) {
        let text = html.replace(/[_]{2,}/g, '<span class="placeholder">Name</span>');
        text = text.replace(/<em>N\.<\/em>/g, '<span class="placeholder">Name</span>');
        return text;
    }

    function tagPronounTargets(html) {
        let text = html;
        for (const entry of PRONOUN_BASE_MARKUP) {
            text = text.replace(
                entry.pattern,
                `<em data-t="${entry.key}">${entry.value}</em>`,
            );
        }
        return text;
    }

    function applyPronounSelection(container, selectedPronoun) {
        const forms = PRONOUN_FORMS[selectedPronoun] || PRONOUN_FORMS.m;
        const targets = container.querySelectorAll("em[data-t]");
        for (const node of targets) {
            const token = node.getAttribute("data-t");
            if (token && forms[token]) {
                node.textContent = forms[token];
            }
        }
    }

    function modernizeTextNodes(container) {
        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
            acceptNode(node) {
                if (!node.nodeValue || !node.nodeValue.trim()) {
                    return NodeFilter.FILTER_REJECT;
                }
                const parent = node.parentElement;
                if (!parent) {
                    return NodeFilter.FILTER_REJECT;
                }
                if (parent.closest("[data-pagefind-meta]")) {
                    return NodeFilter.FILTER_REJECT;
                }
                if (parent.closest("script, style")) {
                    return NodeFilter.FILTER_REJECT;
                }
                return NodeFilter.FILTER_ACCEPT;
            },
        });

        const textNodes = [];
        let current = walker.nextNode();
        while (current) {
            textNodes.push(current);
            current = walker.nextNode();
        }

        for (const node of textNodes) {
            let updated = node.nodeValue || "";
            for (const entry of MODERNIZATION_PATTERNS) {
                entry.pattern.lastIndex = 0;
                updated = updated.replace(entry.pattern, function (match) {
                    return withCase(match, entry.replacement);
                });
            }
            node.nodeValue = updated;
        }
    }

    function hasModernizationCandidate(text) {
        for (const entry of MODERNIZATION_PATTERNS) {
            entry.pattern.lastIndex = 0;
            if (entry.pattern.test(text)) {
                return true;
            }
        }
        return false;
    }

    const state = {
        pronoun: "m",
        modernized: false,
    };

    const rawContent = prayerContent.innerHTML;
    const hasPronounTargets = /<em>(him|his|he|himself|brother)<\/em>/i.test(rawContent);
    const taggedContent = hasPronounTargets ? tagPronounTargets(rawContent) : rawContent;
    const baseTemplateHTML = applyNamePlaceholders(taggedContent);

    const modernizationEligible = pageRoot.dataset.languageModernization === "true";
    const hasModernizableLanguage =
        modernizationEligible && hasModernizationCandidate(rawContent);

    function syncControlState() {
        if (toggleM && toggleF) {
            toggleM.classList.toggle("current", state.pronoun === "m");
            toggleF.classList.toggle("current", state.pronoun === "f");
        }
        if (toggleLanguageOriginal && toggleLanguageModern) {
            toggleLanguageOriginal.classList.toggle("current", !state.modernized);
            toggleLanguageModern.classList.toggle("current", state.modernized);
        }
    }

    function render() {
        const scratch = document.createElement("div");
        scratch.innerHTML = baseTemplateHTML;

        if (hasPronounTargets) {
            applyPronounSelection(scratch, state.pronoun);
        }
        if (hasModernizableLanguage && state.modernized) {
            modernizeTextNodes(scratch);
        }

        prayerContent.innerHTML = scratch.innerHTML;
        syncControlState();
    }

    const showPronounControl = hasPronounTargets && !!pronounControl;
    const showLanguageControl = hasModernizableLanguage && !!languageControl;

    if (pronounControl) {
        pronounControl.hidden = !showPronounControl;
    }
    if (languageControl) {
        languageControl.hidden = !showLanguageControl;
    }
    if (controls) {
        controls.hidden = !(showPronounControl || showLanguageControl);
    }

    if (showPronounControl && toggleF && toggleM) {
        toggleF.addEventListener("click", function () {
            state.pronoun = "f";
            render();
        });
        toggleM.addEventListener("click", function () {
            state.pronoun = "m";
            render();
        });
    }

    if (showLanguageControl && toggleLanguageOriginal && toggleLanguageModern) {
        toggleLanguageOriginal.addEventListener("click", function () {
            state.modernized = false;
            render();
        });
        toggleLanguageModern.addEventListener("click", function () {
            state.modernized = true;
            render();
        });
    }

    render();
})();
