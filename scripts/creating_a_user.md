python -m scripts.provision_test_participants --count 1 --round 1 \
  --pretest-instrument round1_energy_cooling --posttest-instrument round1_energy_cooling \
  --pretest-scenario energy_assistance --tutor-scenario energy_assistance \
  --posttest-scenario cooling_centers --output irb_r1_socratic_participants.csv

  python -m scripts.provision_test_participants --count 1 --round 2 \
  --pretest-instrument round2_packaging_painting --posttest-instrument round2_packaging_painting \
  --pretest-scenario packaging_waste --tutor-scenario packaging_waste \
  --posttest-scenario historical_painting --output irb_r2_socratic_participants.csv


For the control versions, run the same commands with --condition direct_chat added and control instead of socratic in the output filename. The code for each user is printed and saved in its file.
A shortcut: on the live site the real timers apply, so each run takes about 35 minutes. To grab screenshots faster, run the frontend and backend locally with short timers in .env:
PRETEST_MIN_SECONDS=20
PRETEST_SECONDS=120
TUTOR_MIN_SECONDS=30
TUTOR_SECONDS=180
POSTTEST_MIN_SECONDS=20
POSTTEST_SECONDS=120
