# Manual checklist — requires a live notmuch database, which the hermetic test
# suite deliberately never touches (CLAUDE.md §Testing conventions). Run these
# by hand against a real store + real notmuch when validating a release.

@manual
Feature: Merge notmuch tags into zkm mail frontmatter
  As a zkm user who tags mail in notmuch
  I want those tags merged into my mail/messages/ markdown frontmatter
  So that zkm search and entity tooling can see my mail categorisation

  Background:
    Given a zkm store with mail converted by zkm-eml under mail/messages/
    And a notmuch database indexing the same maildir
    And the zkm-notmuch plugin is installed (wheel or dev clone)

  @manual
  Scenario: User tags propagate, system tags do not
    Given a message tagged "bill" and "inbox" in notmuch
    When I run "zkm convert notmuch"
    Then the matching md file's frontmatter tags include "bill"
    And the frontmatter tags do not include "inbox"
    And stderr reports "applied N amendment(s)"
    And a sidecar "<md>.amendments.json" attributes the change to "notmuch"

  @manual
  Scenario: Re-run is a no-op
    Given "zkm convert notmuch" has already been run with an unchanged database
    When I run "zkm convert notmuch" again
    Then "git -C <store> status" shows a clean tree (no diff)

  @manual
  Scenario: Tags for not-yet-converted mail stay queued
    Given notmuch has tags for a message zkm-eml has not converted yet
    When I run "zkm convert notmuch"
    Then stderr reports "N amendment(s) pending (run again after zkm-eml to resolve)"
    And after running "zkm convert eml" followed by "zkm convert notmuch"
    Then the pending amendment is applied and the queue entry is gone

  @manual
  Scenario: Custom notmuch config file
    Given zkm-config.yaml sets notmuch.config_file to a non-default path
    When I run "zkm convert notmuch"
    Then notmuch is invoked with "--config <that path>"

  @manual
  Scenario: Auto-run after eml convert (post-roadmap d0e9)
    Given roadmap item d0e9 is done (plugin.yaml declares kind: amender)
    When I run "zkm convert eml" and new mail files are created
    Then zkm runs the notmuch amender automatically afterwards
    And "zkm convert eml --no-amenders" skips it
