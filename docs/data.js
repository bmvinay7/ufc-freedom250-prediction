window.PREDICTIONS = {
  "event": {
    "name": "UFC Freedom 250",
    "subtitle": "UFC White House",
    "date": "2026-06-14",
    "venue": "South Lawn, The White House",
    "city": "Washington, D.C."
  },
  "model": {
    "name": "XGBoost",
    "test_accuracy": 0.6006314127861089,
    "test_logloss": 0.6662716269493103,
    "baseline_acc": 0.5548539857932123
  },
  "n_sims": 10000,
  "fights": [
    {
      "red": "Ilia Topuria",
      "blue": "Justin Gaethje",
      "weight_class": "Lightweight",
      "scheduled_rounds": 5,
      "billing": "Main Event",
      "title": "UFC Lightweight Title",
      "p_red": 0.6483,
      "p_blue": 0.3517,
      "elo_red": 1711.2,
      "elo_blue": 1670.1,
      "favorite": "Ilia Topuria",
      "fav_prob": 0.6483,
      "confidence": "Lean",
      "elo_edge": 41.1,
      "method_probs": {
        "KO/TKO": 0.4482,
        "Submission": 0.1982,
        "Decision": 0.3536
      },
      "round_probs": [
        0.4044,
        0.2966,
        0.2111,
        0.0623,
        0.0256
      ],
      "likely_method": "KO/TKO",
      "likely_round": 1
    },
    {
      "red": "Alex Pereira",
      "blue": "Ciryl Gane",
      "weight_class": "Heavyweight",
      "scheduled_rounds": 5,
      "billing": "Co-Main",
      "title": "Interim UFC Heavyweight Title",
      "p_red": 0.4855,
      "p_blue": 0.5145,
      "elo_red": 1693.5,
      "elo_blue": 1683.7,
      "favorite": "Ciryl Gane",
      "fav_prob": 0.5145,
      "confidence": "Pick'em",
      "elo_edge": 9.8,
      "method_probs": {
        "KO/TKO": 0.3663,
        "Submission": 0.0939,
        "Decision": 0.5398
      },
      "round_probs": [
        0.3301,
        0.4,
        0.1844,
        0.0109,
        0.0746
      ],
      "likely_method": "Decision",
      "likely_round": 2
    },
    {
      "red": "Sean O'Malley",
      "blue": "Aiemann Zahabi",
      "weight_class": "Bantamweight",
      "scheduled_rounds": 3,
      "billing": "Featured",
      "title": null,
      "p_red": 0.7811,
      "p_blue": 0.2189,
      "elo_red": 1661.7,
      "elo_blue": 1626.0,
      "favorite": "Sean O'Malley",
      "fav_prob": 0.7811,
      "confidence": "Heavy Favorite",
      "elo_edge": 35.7,
      "method_probs": {
        "KO/TKO": 0.4952,
        "Submission": 0.1084,
        "Decision": 0.3965
      },
      "round_probs": [
        0.3958,
        0.3584,
        0.2458
      ],
      "likely_method": "KO/TKO",
      "likely_round": 1
    },
    {
      "red": "Josh Hokit",
      "blue": "Derrick Lewis",
      "weight_class": "Heavyweight",
      "scheduled_rounds": 3,
      "billing": "Featured",
      "title": null,
      "p_red": 0.8022,
      "p_blue": 0.1978,
      "elo_red": 1588.9,
      "elo_blue": 1612.9,
      "favorite": "Josh Hokit",
      "fav_prob": 0.8022,
      "confidence": "Heavy Favorite",
      "elo_edge": 24.0,
      "method_probs": {
        "KO/TKO": 0.4399,
        "Submission": 0.1352,
        "Decision": 0.4249
      },
      "round_probs": [
        0.5004,
        0.2634,
        0.2362
      ],
      "likely_method": "KO/TKO",
      "likely_round": 1
    },
    {
      "red": "Maur\u00edcio Ruffy",
      "blue": "Michael Chandler",
      "weight_class": "Lightweight",
      "scheduled_rounds": 3,
      "billing": "Featured",
      "title": null,
      "p_red": 0.7929,
      "p_blue": 0.2071,
      "elo_red": 1565.9,
      "elo_blue": 1498.7,
      "favorite": "Maur\u00edcio Ruffy",
      "fav_prob": 0.7929,
      "confidence": "Heavy Favorite",
      "elo_edge": 67.2,
      "method_probs": {
        "KO/TKO": 0.3641,
        "Submission": 0.2119,
        "Decision": 0.424
      },
      "round_probs": [
        0.5823,
        0.2695,
        0.1482
      ],
      "likely_method": "Decision",
      "likely_round": 1
    },
    {
      "red": "Bo Nickal",
      "blue": "Kyle Daukaus",
      "weight_class": "Middleweight",
      "scheduled_rounds": 3,
      "billing": "Featured",
      "title": null,
      "p_red": 0.7502,
      "p_blue": 0.2498,
      "elo_red": 1577.1,
      "elo_blue": 1518.9,
      "favorite": "Bo Nickal",
      "fav_prob": 0.7502,
      "confidence": "Heavy Favorite",
      "elo_edge": 58.2,
      "method_probs": {
        "KO/TKO": 0.3653,
        "Submission": 0.128,
        "Decision": 0.5067
      },
      "round_probs": [
        0.5133,
        0.3384,
        0.1482
      ],
      "likely_method": "Decision",
      "likely_round": 1
    },
    {
      "red": "Diego Lopes",
      "blue": "Steve Garcia",
      "weight_class": "Featherweight",
      "scheduled_rounds": 3,
      "billing": "Featured",
      "title": null,
      "p_red": 0.5661,
      "p_blue": 0.4339,
      "elo_red": 1600.3,
      "elo_blue": 1624.8,
      "favorite": "Diego Lopes",
      "fav_prob": 0.5661,
      "confidence": "Lean",
      "elo_edge": 24.5,
      "method_probs": {
        "KO/TKO": 0.2388,
        "Submission": 0.2835,
        "Decision": 0.4777
      },
      "round_probs": [
        0.5012,
        0.3534,
        0.1454
      ],
      "likely_method": "Decision",
      "likely_round": 1
    }
  ],
  "simulation": {
    "n_sims": 10000,
    "fav_wins_distribution": {
      "0": 0.0001,
      "1": 0.0042,
      "2": 0.0233,
      "3": 0.1019,
      "4": 0.2381,
      "5": 0.3246,
      "6": 0.2387,
      "7": 0.0691
    },
    "expected_favorites_correct": 4.848,
    "favorites_correct_95ci": [
      2,
      7
    ],
    "all_chalk_prob": 0.0691,
    "all_chalk_parlay_decimal_odds": 14.2,
    "expected_upsets": 2.152,
    "most_likely_outcomes": [
      {
        "winners": [
          "Ilia Topuria",
          "Ciryl Gane",
          "Sean O'Malley",
          "Josh Hokit",
          "Maur\u00edcio Ruffy",
          "Bo Nickal",
          "Diego Lopes"
        ],
        "n_upsets": 0,
        "prob": 0.0691
      },
      {
        "winners": [
          "Ilia Topuria",
          "Alex Pereira",
          "Sean O'Malley",
          "Josh Hokit",
          "Maur\u00edcio Ruffy",
          "Bo Nickal",
          "Diego Lopes"
        ],
        "n_upsets": 1,
        "prob": 0.0671
      },
      {
        "winners": [
          "Ilia Topuria",
          "Ciryl Gane",
          "Sean O'Malley",
          "Josh Hokit",
          "Maur\u00edcio Ruffy",
          "Bo Nickal",
          "Steve Garcia"
        ],
        "n_upsets": 1,
        "prob": 0.0537
      },
      {
        "winners": [
          "Ilia Topuria",
          "Alex Pereira",
          "Sean O'Malley",
          "Josh Hokit",
          "Maur\u00edcio Ruffy",
          "Bo Nickal",
          "Steve Garcia"
        ],
        "n_upsets": 2,
        "prob": 0.0516
      },
      {
        "winners": [
          "Justin Gaethje",
          "Ciryl Gane",
          "Sean O'Malley",
          "Josh Hokit",
          "Maur\u00edcio Ruffy",
          "Bo Nickal",
          "Diego Lopes"
        ],
        "n_upsets": 1,
        "prob": 0.0378
      }
    ]
  }
};
