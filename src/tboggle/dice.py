class DiceSet:
    def __init__(self, name, desc, num, dice):
        self.name = name
        self.desc = desc
        self.num = num
        self.dice = dice

    @classmethod
    def get_by_name(cls, name):
        for d in sets:
            if d.name == name:
                return d
        return None

    def get_face_display(self, face):
        if face == "0":
            raise NotImplementedError()
        elif face == '1':
            return "Qu"
        elif face == '2':
            return "In"
        elif face == "3":
            return "Th"
        elif face == "4":
            return "Er"
        elif face == "5":
            return "He"
        elif face == "6":
            return "An"
        else:
            return f"{face} "


# #0 = Blank 1 = Qu 2 = In 3 = Th 4 = Er 5 = He 6 = An


# noinspection SpellCheckingInspection
sets = [
    DiceSet(
        "4-classic",
        "4x4 Classic",
        4,
        [
            "AACIOT", "ABILTY", "ABJMOQ", "ACDEMP",
            "ACELRS", "ADENVZ", "AHMORS", "BIFORX",
            "DENOSW", "DKNOTU", "EEFHIY", "EGKLUY",
            "EGINTV", "EHINPS", "ELPSTU", "GILRUW",
        ]),

    DiceSet(
        "4",
        "4x4 Revised",
        4,
        [
            "AAEEGN", "ABBJOO", "ACHOPS", "AFFKPS",
            "AOOTTW", "CIMOTU", "DEILRX", "DELRVY",
            "DISTTY", "EEGHNW", "EEINSU", "EHRTVW",
            "EIOSST", "ELRTTY", "HIMNU1", "HLNNRZ",
        ]),

    DiceSet(
        "5-orig",
        "5x5 Original",
        5,
        [
            "AAAFRS", "AAEEEE", "AAFIRS", "ADENNN", "AEEEEM",
            "AEEGMU", "AEGMNN", "AFIRSY", "BJK1XZ", "CCENST",
            "CEIILT", "CEIPST", "DDHNOT", "DHHLOR", "DHHLOR",
            "DHLNOR", "EIIITT", "CEILPT", "EMOTTT", "ENSSSU",
            "FIPRSY", "GORRVW", "IPRRRY", "NOOTUW", "OOOTTU",
        ]),

    DiceSet(
        "5-challenge",
        "5x5 Challenge",
        5,
        [
            "AAAFRS", "AAEEEE", "AAFIRS", "ADENNN", "AEEEEM",
            "AEEGMU", "AEGMNN", "AFIRSY", "BJK1XZ", "CCENST",
            "CEIILT", "CEIPST", "DDHNOT", "DHHLOR", "IKLM1U",
            "DHLNOR", "EIIITT", "CEILPT", "EMOTTT", "ENSSSU",
            "FIPRSY", "GORRVW", "IPRRRY", "NOOTUW", "OOOTTU",
        ]),

    DiceSet(
        "5-big-deluxe",
        "5x5 Big Deluxe",
        5,
        [
            "AAAFRS", "AAEEEE", "AAFIRS", "ADENNN", "AEEEEM",
            "AEEGMU", "AEGMNN", "AFIRSY", "BJK1XZ", "CCNSTW",
            "CEIILT", "CEIPST", "DDLNOR", "DHHLOR", "DHHNOT",
            "DHLNOR", "EIIITT", "CEILPT", "EMOTTT", "ENSSSU",
            "FIPRSY", "GORRVW", "HIPRRY", "NOOTUW", "OOOTTU",
        ]),

    DiceSet(
        "5",
        "5x5 Big 2012",
        5,
        [
            "AAAFRS", "AAEEEE", "AAFIRS", "ADENNN", "AEEEEM",
            "AEEGMU", "AEGMNN", "AFIRSY", "BBJKXZ", "CCENST",
            "EIILST", "CEIPST", "DDHNOT", "DHHLOR", "DHHNOW",
            "DHLNOR", "EIIITT", "EILPST", "EMOTTT", "ENSSSU",
            "123456", "GORRVW", "IPRSYY", "NOOTUW", "OOOTTU",
        ]),

    DiceSet(
        "6-super",
        "6x6 Super Big",
        6,
        [
            "AAAFRS", "AAEEEE", "AAEEOO", "AAFIRS", "ABDEIO", "ADENNN",
            "AEEEEM", "AEEGMU", "AEGMNN", "AEILMN", "AEINOU", "AFIRSY",
            "123456", "BBJKXZ", "CCENST", "CDDLNN", "CEIITT", "CEIPST",
            "CFGNUY", "DDHNOT", "DHHLOR", "DHHNOW", "DHLNOR", "EHILRS",
            "EIILST", "EILPST", "EIO000", "EMTTTO", "ENSSSU", "GORRVW",
            "HIRSTV", "HOPRST", "IPRSYY", "JK1WXZ", "NOOTUW", "OOOTTU",
        ]),

    DiceSet(
        "6",
        "6x6 Super Big Simple",
        6,
        [
            "AAAFRS", "AAEEEE", "AAEEOO", "AAFIRS", "ABDEIO", "ADENNN",
            "AEEEEM", "AEEGMU", "AEGMNN", "AEILMN", "AEINOU", "AFIRSY",
            "AEIOUS", "BBJKXZ", "CCENST", "CDDLNN", "CEIITT", "CEIPST",  # 1st
            "CFGNUY", "DDHNOT", "DHHLOR", "DHHNOW", "DHLNOR", "EHILRS",
            "EIILST", "EILPST", "EIOSSS", "EMTTTO", "ENSSSU", "GORRVW",  # 3rd
            "HIRSTV", "HOPRST", "IPRSYY", "JK1WXZ", "NOOTUW", "OOOTTU",
        ]),
]
